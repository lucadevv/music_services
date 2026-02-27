"""Shared fixtures for YouTube Music Service tests."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import Settings
from app.core.cache import clear_cache


# ============================================================================
# Event Loop
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings Fixtures
# ============================================================================

@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        API_V1_STR="/api/v1",
        PROJECT_NAME="Test YouTube Music Service",
        VERSION="1.0.0-test",
        BROWSER_JSON_PATH="browser.json",
        CORS_ORIGINS="*",
        CORS_ALLOW_CREDENTIALS=True,
        CORS_ALLOW_METHODS="*",
        CORS_ALLOW_HEADERS="*",
        HOST="0.0.0.0",
        PORT=8000,
        RATE_LIMIT_ENABLED=False,  # Disable rate limiting for tests
        RATE_LIMIT_PER_MINUTE=60,
        RATE_LIMIT_PER_HOUR=1000,
        CACHE_ENABLED=False,  # Disable cache for tests by default
        CACHE_BACKEND="memory",
        CACHE_TTL=300,
        CACHE_MAX_SIZE=1000,
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_DB=0,
        REDIS_PASSWORD=None,
        HTTP_TIMEOUT=30,
        HTTP_MAX_CONNECTIONS=100,
        HTTP_MAX_KEEPALIVE_CONNECTIONS=20,
        ENABLE_COMPRESSION=False,
        MAX_WORKERS=10,
    )


@pytest.fixture
def mock_settings_with_cache(mock_settings: Settings) -> Settings:
    """Create mock settings with cache enabled."""
    mock_settings.CACHE_ENABLED = True
    return mock_settings


# ============================================================================
# YTMusic Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ytmusic():
    """Create mock YTMusic client."""
    mock = MagicMock()
    
    # Search methods
    mock.search.return_value = []
    mock.get_search_suggestions.return_value = []
    mock.remove_search_suggestions.return_value = True
    
    # Browse methods
    mock.get_home.return_value = []
    mock.get_artist.return_value = {}
    mock.get_artist_albums.return_value = {}
    mock.get_album.return_value = {}
    mock.get_album_browse_id.return_value = None
    mock.get_song.return_value = {}
    mock.get_song_related.return_value = []
    mock.get_lyrics.return_value = {}
    
    # Explore methods
    mock.get_mood_categories.return_value = {}
    mock.get_mood_playlists.return_value = []
    mock.get_charts.return_value = {}
    
    # Playlist methods
    mock.get_playlist.return_value = {}
    
    # Watch methods
    mock.get_watch_playlist.return_value = {}
    
    # Podcast methods
    mock.get_channel.return_value = {}
    mock.get_channel_episodes.return_value = {}
    mock.get_podcast.return_value = {}
    mock.get_episode.return_value = {}
    mock.get_episodes_playlist.return_value = {}
    
    # Library/Upload methods
    mock.get_library_upload_songs.return_value = []
    mock.get_library_upload_artists.return_value = []
    mock.get_library_upload_albums.return_value = []
    mock.get_library_upload_artist.return_value = {}
    mock.get_library_upload_album.return_value = {}
    mock.upload_song.return_value = {}
    mock.delete_upload_entity.return_value = True
    
    return mock


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_song() -> Dict[str, Any]:
    """Sample song data for testing."""
    return {
        "videoId": "abc123xyz",
        "title": "Test Song",
        "artists": [{"name": "Test Artist", "id": "UC123"}],
        "album": {"name": "Test Album", "id": "MPREb123"},
        "duration": "3:45",
        "duration_seconds": 225,
        "thumbnails": [
            {"url": "https://example.com/thumb1.jpg", "width": 120, "height": 90},
            {"url": "https://example.com/thumb2.jpg", "width": 480, "height": 360},
        ],
        "views": "1M",
    }


@pytest.fixture
def sample_artist() -> Dict[str, Any]:
    """Sample artist data for testing."""
    return {
        "description": "Test Artist Description",
        "name": "Test Artist",
        "channelId": "UC123456789",
        "thumbnails": [
            {"url": "https://example.com/artist.jpg", "width": 400, "height": 400}
        ],
        "views": "10M",
        "subscribers": "500K",
        "top_releases": {},
        "related": [],
    }


@pytest.fixture
def sample_album() -> Dict[str, Any]:
    """Sample album data for testing."""
    return {
        "title": "Test Album",
        "description": "Test Album Description",
        "artists": [{"name": "Test Artist", "id": "UC123"}],
        "year": "2024",
        "trackCount": 10,
        "duration": "35:00",
        "thumbnails": [
            {"url": "https://example.com/album.jpg", "width": 500, "height": 500}
        ],
        "tracks": [
            {
                "videoId": "track1",
                "title": "Track 1",
                "artists": [{"name": "Test Artist"}],
                "duration": "3:30",
            },
            {
                "videoId": "track2",
                "title": "Track 2",
                "artists": [{"name": "Test Artist"}],
                "duration": "4:15",
            },
        ],
        "audioPlaylistId": "PL123",
    }


@pytest.fixture
def sample_playlist() -> Dict[str, Any]:
    """Sample playlist data for testing."""
    return {
        "id": "PL123456789",
        "title": "Test Playlist",
        "description": "A test playlist",
        "author": {"name": "Test User", "id": "UC999"},
        "trackCount": 5,
        "duration": "18:30",
        "thumbnails": [
            {"url": "https://example.com/playlist.jpg", "width": 400, "height": 400}
        ],
        "tracks": [
            {
                "videoId": "song1",
                "title": "Playlist Song 1",
                "artists": [{"name": "Artist 1"}],
                "duration": "3:30",
            },
        ],
        "views": "1000",
        "privacy": "PUBLIC",
    }


@pytest.fixture
def sample_search_results() -> List[Dict[str, Any]]:
    """Sample search results for testing."""
    return [
        {
            "videoId": "result1",
            "title": "Search Result 1",
            "artists": [{"name": "Artist 1"}],
            "resultType": "song",
            "duration": "3:45",
        },
        {
            "videoId": "result2",
            "title": "Search Result 2",
            "artists": [{"name": "Artist 2"}],
            "resultType": "song",
            "duration": "4:00",
        },
        {
            "browseId": "album1",
            "title": "Album Result",
            "artists": [{"name": "Artist 3"}],
            "resultType": "album",
        },
    ]


@pytest.fixture
def sample_suggestions() -> List[str]:
    """Sample search suggestions for testing."""
    return [
        "test query 1",
        "test query 2",
        "test query 3",
    ]


@pytest.fixture
def sample_home_content() -> List[Dict[str, Any]]:
    """Sample home content for testing."""
    return [
        {
            "title": "Listen Again",
            "contents": [
                {"videoId": "home1", "title": "Home Song 1"},
                {"videoId": "home2", "title": "Home Song 2"},
            ],
        },
        {
            "title": "Moods & Genres",
            "contents": [
                {"title": "Cumbia", "params": "ggMPOg1uX3hRRFdlaEhHU09k"},
                {"title": "Rock", "params": "abc123"},
            ],
        },
    ]


@pytest.fixture
def sample_mood_categories() -> Dict[str, List[Dict[str, Any]]]:
    """Sample mood categories for testing."""
    return {
        "For you": [
            {"title": "Your Mix", "params": "mix1"},
        ],
        "Genres": [
            {"title": "Cumbia", "params": "ggMPOg1uX3hRRFdlaEhHU09k"},
            {"title": "Rock", "params": "rock1"},
        ],
        "Moods & moments": [
            {"title": "Chill", "params": "chill1"},
            {"title": "Workout", "params": "workout1"},
        ],
    }


@pytest.fixture
def sample_charts() -> Dict[str, Any]:
    """Sample charts data for testing."""
    return {
        "top_songs": [
            {"videoId": "chart1", "title": "Top Song 1", "rank": 1},
            {"videoId": "chart2", "title": "Top Song 2", "rank": 2},
        ],
        "trending": [
            {"videoId": "trend1", "title": "Trending 1"},
        ],
        "country": "US",
    }


@pytest.fixture
def sample_podcast() -> Dict[str, Any]:
    """Sample podcast data for testing."""
    return {
        "id": "podcast123",
        "title": "Test Podcast",
        "description": "A test podcast",
        "author": "Test Podcaster",
        "thumbnails": [
            {"url": "https://example.com/podcast.jpg", "width": 400, "height": 400}
        ],
        "episodes": [
            {
                "videoId": "episode1",
                "title": "Episode 1",
                "description": "First episode",
                "duration": "45:00",
            },
        ],
    }


@pytest.fixture
def sample_episode() -> Dict[str, Any]:
    """Sample episode data for testing."""
    return {
        "videoId": "episode1",
        "title": "Test Episode",
        "description": "A test episode",
        "duration": "45:00",
        "thumbnails": [
            {"url": "https://example.com/episode.jpg", "width": 400, "height": 400}
        ],
        "published_at": "2024-01-15",
        "podcast": {"title": "Test Podcast", "id": "podcast123"},
    }


# ============================================================================
# Test Client Fixtures
# ============================================================================

@pytest.fixture
def test_client(mock_ytmusic) -> TestClient:
    """Create synchronous test client with mocked YTMusic."""
    from app.core.ytmusic_client import get_ytmusic
    
    # Override the YTMusic dependency
    app.dependency_overrides[get_ytmusic] = lambda: mock_ytmusic
    
    with TestClient(app) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(mock_ytmusic):
    """Create async test client with mocked YTMusic."""
    from app.core.ytmusic_client import get_ytmusic
    
    # Override the YTMusic dependency
    app.dependency_overrides[get_ytmusic] = lambda: mock_ytmusic
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


# ============================================================================
# Cache Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_cache():
    """Reset cache before each test."""
    clear_cache()
    yield
    clear_cache()


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def mock_circuit_breaker():
    """Create mock circuit breaker."""
    with patch("app.services.stream_service.youtube_stream_circuit") as mock:
        mock.is_open.return_value = False
        mock.get_status.return_value = {
            "state": "closed",
            "failure_count": 0,
            "remaining_time_seconds": 0,
            "is_blocked": False,
        }
        mock.record_success.return_value = None
        mock.record_failure.return_value = None
        yield mock


@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp for stream tests."""
    with patch("app.services.stream_service.yt_dlp") as mock:
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
        mock.YoutubeDL.return_value.__enter__.return_value = mock_ydl
        yield mock


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_ytmusic_with_search_results(results: List[Dict]) -> MagicMock:
    """Create a mock YTMusic client with specific search results."""
    mock = MagicMock()
    mock.search.return_value = results
    return mock


def create_mock_ytmusic_with_error(error: Exception) -> MagicMock:
    """Create a mock YTMusic client that raises an error."""
    mock = MagicMock()
    mock.search.side_effect = error
    return mock


# ============================================================================
# Service Mock Classes
# ============================================================================

class MockBrowseService:
    """Mock BrowseService for integration tests."""
    
    def __init__(self):
        self._get_home_return = []
        self._get_artist_return = {}
        self._get_artist_albums_return = {}
        self._get_album_return = {}
        self._get_album_browse_id_return = None
        self._get_song_return = {}
        self._get_song_related_return = []
        self._get_lyrics_return = {}
        
        self._get_home_side_effect = None
        self._get_artist_side_effect = None
        self._get_artist_albums_side_effect = None
        self._get_album_side_effect = None
        self._get_album_browse_id_side_effect = None
        self._get_song_side_effect = None
        self._get_song_related_side_effect = None
        self._get_lyrics_side_effect = None
    
    async def get_home(self):
        if self._get_home_side_effect:
            raise self._get_home_side_effect
        return self._get_home_return
    
    async def get_artist(self, channel_id: str):
        if self._get_artist_side_effect:
            raise self._get_artist_side_effect
        return self._get_artist_return
    
    async def get_artist_albums(self, channel_id: str, params=None):
        if self._get_artist_albums_side_effect:
            raise self._get_artist_albums_side_effect
        return self._get_artist_albums_return
    
    async def get_album(self, album_id: str):
        if self._get_album_side_effect:
            raise self._get_album_side_effect
        return self._get_album_return
    
    async def get_album_browse_id(self, album_id: str):
        if self._get_album_browse_id_side_effect:
            raise self._get_album_browse_id_side_effect
        return self._get_album_browse_id_return
    
    async def get_song(self, video_id: str, signature_timestamp=None):
        if self._get_song_side_effect:
            raise self._get_song_side_effect
        return self._get_song_return
    
    async def get_song_related(self, video_id: str):
        if self._get_song_related_side_effect:
            raise self._get_song_related_side_effect
        return self._get_song_related_return
    
    async def get_lyrics(self, browse_id: str):
        if self._get_lyrics_side_effect:
            raise self._get_lyrics_side_effect
        return self._get_lyrics_return


class MockSearchService:
    """Mock SearchService for integration tests."""
    
    def __init__(self):
        self._search_return = []
        self._get_search_suggestions_return = []
        self._remove_search_suggestions_return = True
        
        self._search_side_effect = None
        self._get_search_suggestions_side_effect = None
        self._remove_search_suggestions_side_effect = None
    
    async def search(self, query, filter=None, scope=None, limit=20, ignore_spelling=False):
        if self._search_side_effect:
            raise self._search_side_effect
        return self._search_return
    
    async def get_search_suggestions(self, query: str):
        if self._get_search_suggestions_side_effect:
            raise self._get_search_suggestions_side_effect
        return self._get_search_suggestions_return
    
    async def remove_search_suggestions(self, query: str):
        if self._remove_search_suggestions_side_effect:
            raise self._remove_search_suggestions_side_effect
        return self._remove_search_suggestions_return


class MockStreamService:
    """Mock StreamService for integration tests."""
    
    def __init__(self):
        self._get_stream_url_return = {}
        self._enrich_items_with_streams_return = []
        
        self._get_stream_url_side_effect = None
        self._enrich_items_with_streams_side_effect = None
    
    async def get_stream_url(self, video_id: str):
        if self._get_stream_url_side_effect:
            raise self._get_stream_url_side_effect
        return self._get_stream_url_return
    
    async def enrich_items_with_streams(self, items, include_stream_urls=True):
        if self._enrich_items_with_streams_side_effect:
            raise self._enrich_items_with_streams_side_effect
        return self._enrich_items_with_streams_return


# ============================================================================
# Mock Service Fixtures with Dependency Overrides
# ============================================================================

@pytest.fixture
def mock_browse_service():
    """Create a mock BrowseService instance."""
    return MockBrowseService()


@pytest.fixture
def mock_search_service():
    """Create a mock SearchService instance."""
    return MockSearchService()


@pytest.fixture
def mock_stream_service_instance():
    """Create a mock StreamService instance."""
    return MockStreamService()


@pytest.fixture
def test_client_with_browse_mocks(mock_browse_service, mock_stream_service_instance):
    """Create test client with mocked browse and stream services."""
    from app.api.v1.endpoints import browse
    from app.api.v1.endpoints.browse import get_browse_service, get_stream_service
    
    app.dependency_overrides[get_browse_service] = lambda: mock_browse_service
    app.dependency_overrides[get_stream_service] = lambda: mock_stream_service_instance
    
    with TestClient(app) as client:
        yield client, mock_browse_service, mock_stream_service_instance
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_with_search_mocks(mock_search_service, mock_stream_service_instance):
    """Create test client with mocked search and stream services."""
    from app.api.v1.endpoints.search import get_search_service, get_stream_service
    
    app.dependency_overrides[get_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_stream_service] = lambda: mock_stream_service_instance
    
    with TestClient(app) as client:
        yield client, mock_search_service, mock_stream_service_instance
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_with_stream_mocks(mock_stream_service_instance):
    """Create test client with mocked stream service."""
    from app.api.v1.endpoints.stream import get_stream_service
    
    app.dependency_overrides[get_stream_service] = lambda: mock_stream_service_instance
    
    with TestClient(app) as client:
        yield client, mock_stream_service_instance
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_circuit_breaker_for_integration():
    """Mock circuit breaker for integration tests."""
    with patch("app.api.v1.endpoints.stream.youtube_stream_circuit") as mock:
        mock.is_open.return_value = False
        mock.get_status.return_value = {
            "state": "closed",
            "failure_count": 0,
            "remaining_time_seconds": 0,
            "is_blocked": False,
        }
        mock.record_success.return_value = None
        mock.record_failure.return_value = None
        yield mock
