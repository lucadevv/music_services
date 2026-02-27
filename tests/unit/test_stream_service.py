"""Unit tests for StreamService."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import time

from app.services.stream_service import StreamService
from app.core.circuit_breaker import CircuitState
from app.core.exceptions import CircuitBreakerError, RateLimitError, ExternalServiceError


@pytest.mark.asyncio
class TestStreamService:
    """Test cases for StreamService class."""

    def test_init(self):
        """Test StreamService initialization."""
        service = StreamService()
        
        assert service.settings is not None
        assert service._ytmusic is None

    def test_metadata_cache_key(self):
        """Test metadata cache key generation."""
        service = StreamService()
        
        key = service._get_metadata_cache_key("video123")
        
        assert key == "stream_metadata:video123"

    def test_stream_url_cache_key(self):
        """Test stream URL cache key generation."""
        service = StreamService()
        
        key = service._get_stream_url_cache_key("video123")
        
        assert key == "stream_url:video123"


@pytest.mark.asyncio
class TestStreamServiceCaching:
    """Test caching behavior for StreamService."""

    @patch("app.services.stream_service.cache_module")
    async def test_get_cached_metadata_when_disabled(self, mock_cache):
        """Test metadata cache returns None when cache is disabled."""
        service = StreamService()
        service.settings.CACHE_ENABLED = False
        
        result = service._get_cached_metadata("video123")
        
        assert result is None

    @patch("app.services.stream_service.cache_module")
    async def test_get_cached_metadata_cache_miss(self, mock_cache):
        """Test metadata cache returns None on cache miss."""
        service = StreamService()
        service.settings.CACHE_ENABLED = True
        mock_cache.has_cached_key.return_value = False
        
        result = service._get_cached_metadata("video123")
        
        assert result is None

    @patch("app.services.stream_service.cache_module")
    async def test_get_cached_metadata_expired(self, mock_cache):
        """Test metadata cache returns None when expired."""
        service = StreamService()
        service.settings.CACHE_ENABLED = True
        mock_cache.has_cached_key.return_value = True
        mock_cache.get_cached_timestamp.return_value = time.time() - 100000  # Expired
        mock_cache.get_cached_value.return_value = {"title": "Test"}
        
        result = service._get_cached_metadata("video123")
        
        assert result is None

    @patch("app.services.stream_service.cache_module")
    async def test_get_cached_metadata_hit(self, mock_cache):
        """Test metadata cache returns value on cache hit."""
        service = StreamService()
        service.settings.CACHE_ENABLED = True
        mock_cache.has_cached_key.return_value = True
        mock_cache.get_cached_timestamp.return_value = time.time()  # Fresh
        mock_cache.get_cached_value.return_value = {"title": "Test"}
        
        result = service._get_cached_metadata("video123")
        
        assert result == {"title": "Test"}

    @patch("app.services.stream_service.cache_module")
    async def test_cache_metadata(self, mock_cache):
        """Test caching metadata."""
        service = StreamService()
        service.settings.CACHE_ENABLED = True
        
        service._cache_metadata("video123", {"title": "Test"})
        
        mock_cache.set_cached_value.assert_called_once()

    @patch("app.services.stream_service.cache_module")
    async def test_cache_metadata_disabled(self, mock_cache):
        """Test caching metadata when cache is disabled."""
        service = StreamService()
        service.settings.CACHE_ENABLED = False
        
        service._cache_metadata("video123", {"title": "Test"})
        
        mock_cache.set_cached_value.assert_not_called()


@pytest.mark.asyncio
class TestGetStreamUrl:
    """Test cases for get_stream_url method."""

    @patch("app.services.stream_service.youtube_stream_circuit")
    @patch("app.services.stream_service.yt_dlp")
    async def test_get_stream_url_success(self, mock_ytdlp, mock_circuit):
        """Test successful stream URL retrieval."""
        mock_circuit.is_open.return_value = False
        
        # Mock yt-dlp
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
            "adaptive_formats": [
                {
                    "acodec": "opus",
                    "vcodec": "none",
                    "url": "https://example.com/audio.m4a",
                }
            ],
            "formats": [],
        }
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        
        service = StreamService()
        result = await service.get_stream_url("video123")
        
        assert "url" in result
        assert result["url"] == "https://example.com/audio.m4a"
        assert result["title"] == "Test Song"
        assert result["artist"] == "Test Artist"
        mock_circuit.record_success.assert_called_once()

    @patch("app.services.stream_service.youtube_stream_circuit")
    async def test_get_stream_url_circuit_open(self, mock_circuit):
        """Test stream URL when circuit breaker is open."""
        mock_circuit.is_open.return_value = True
        mock_circuit.get_status.return_value = {
            "state": "open",
            "remaining_time_seconds": 300,
        }
        
        service = StreamService()
        
        with pytest.raises(CircuitBreakerError):
            await service.get_stream_url("video123")

    @patch("app.services.stream_service.youtube_stream_circuit")
    @patch("app.services.stream_service.yt_dlp")
    async def test_get_stream_url_rate_limit_error(self, mock_ytdlp, mock_circuit):
        """Test stream URL handles rate limit errors."""
        mock_circuit.is_open.return_value = False
        
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = Exception("429 Rate limit exceeded")
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        
        mock_circuit.get_status.return_value = {
            "state": "open",
            "remaining_time_seconds": 600,
        }
        
        service = StreamService()
        
        with pytest.raises(RateLimitError):
            await service.get_stream_url("video123")
        
        mock_circuit.record_failure.assert_called_once()

    @patch("app.services.stream_service.youtube_stream_circuit")
    @patch("app.services.stream_service.yt_dlp")
    async def test_get_stream_url_no_audio_format(self, mock_ytdlp, mock_circuit):
        """Test stream URL when no audio format found."""
        mock_circuit.is_open.return_value = False
        
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Test",
            "adaptive_formats": [],  # No audio
            "formats": [],  # No formats
        }
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        
        service = StreamService()
        
        with pytest.raises(ExternalServiceError):
            await service.get_stream_url("video123")

    @patch("app.services.stream_service.youtube_stream_circuit")
    @patch("app.services.stream_service.yt_dlp")
    async def test_get_stream_url_fallback_to_formats(self, mock_ytdlp, mock_circuit):
        """Test stream URL fallback to formats when adaptive_formats empty."""
        mock_circuit.is_open.return_value = False
        
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
            "adaptive_formats": [],  # Empty
            "formats": [
                {
                    "acodec": "opus",
                    "url": "https://example.com/fallback.m4a",
                }
            ],
        }
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        
        service = StreamService()
        result = await service.get_stream_url("video123")
        
        assert result["url"] == "https://example.com/fallback.m4a"


@pytest.mark.asyncio
class TestThumbnailExtraction:
    """Test thumbnail extraction from items."""

    def test_get_best_thumbnail_from_thumbnails_list(self):
        """Test extracting best thumbnail from thumbnails list."""
        service = StreamService()
        
        item = {
            "thumbnails": [
                {"url": "https://example.com/small.jpg", "width": 120, "height": 90},
                {"url": "https://example.com/large.jpg", "width": 480, "height": 360},
                {"url": "https://example.com/medium.jpg", "width": 320, "height": 180},
            ]
        }
        
        result = service._get_best_thumbnail(item)
        
        # Should return the largest (480x360)
        assert result == "https://example.com/large.jpg"

    def test_get_best_thumbnail_empty_thumbnails(self):
        """Test thumbnail extraction with empty thumbnails."""
        service = StreamService()
        
        item = {"thumbnails": []}
        
        result = service._get_best_thumbnail(item)
        
        assert result is None

    def test_get_best_thumbnail_no_thumbnails(self):
        """Test thumbnail extraction with no thumbnails field."""
        service = StreamService()
        
        item = {}
        
        result = service._get_best_thumbnail(item)
        
        assert result is None

    def test_get_best_thumbnail_string_thumbnail(self):
        """Test thumbnail extraction with string thumbnail."""
        service = StreamService()
        
        item = {"thumbnail": "https://example.com/string.jpg"}
        
        result = service._get_best_thumbnail(item)
        
        assert result == "https://example.com/string.jpg"


@pytest.mark.asyncio
class TestEnrichItems:
    """Test items enrichment with stream URLs."""

    @patch("app.services.stream_service.youtube_stream_circuit")
    @patch("app.services.stream_service.yt_dlp")
    async def test_enrich_items_with_streams(self, mock_ytdlp, mock_circuit):
        """Test enriching items with stream URLs."""
        mock_circuit.is_open.return_value = False
        
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Test",
            "adaptive_formats": [
                {"acodec": "opus", "vcodec": "none", "url": "https://audio.m4a"}
            ],
            "formats": [],
        }
        mock_ytdlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        
        service = StreamService()
        items = [
            {"videoId": "video1", "title": "Song 1"},
            {"videoId": "video2", "title": "Song 2"},
        ]
        
        result = await service.enrich_items_with_streams(items, include_stream_urls=True)
        
        assert len(result) == 2
        assert result[0]["stream_url"] == "https://audio.m4a"
        assert result[1]["stream_url"] == "https://audio.m4a"

    async def test_enrich_items_without_stream_urls(self):
        """Test enriching items without stream URLs."""
        service = StreamService()
        items = [
            {"videoId": "video1", "title": "Song 1", "thumbnails": []},
        ]
        
        result = await service.enrich_items_with_streams(items, include_stream_urls=False)
        
        assert len(result) == 1
        assert "stream_url" not in result[0]

    async def test_enrich_items_empty_list(self):
        """Test enriching empty items list."""
        service = StreamService()
        
        result = await service.enrich_items_with_streams([], include_stream_urls=True)
        
        assert result == []

    async def test_enrich_items_without_video_id(self):
        """Test enriching items without video IDs."""
        service = StreamService()
        items = [
            {"title": "No Video ID", "thumbnails": []},
        ]
        
        result = await service.enrich_items_with_streams(items, include_stream_urls=True)
        
        assert len(result) == 1
        assert "stream_url" not in result[0]
