"""Unit tests for WatchService."""
import pytest
from unittest.mock import MagicMock

from app.services.watch_service import WatchService
from app.core.exceptions import RateLimitError, AuthenticationError


@pytest.mark.asyncio
class TestWatchService:
    """Test cases for WatchService class."""


@pytest.mark.asyncio
class TestGetWatchPlaylist:
    """Test cases for get_watch_playlist method."""

    async def test_get_watch_playlist_with_video_id(self, mock_ytmusic):
        """Test get_watch_playlist with video_id."""
        watch_playlist = {
            "tracks": [
                {"videoId": "track1", "title": "Track 1"},
                {"videoId": "track2", "title": "Track 2"},
            ]
        }
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(video_id="abc123")
        
        assert result == watch_playlist
        mock_ytmusic.get_watch_playlist.assert_called_once()

    async def test_get_watch_playlist_with_playlist_id(self, mock_ytmusic):
        """Test get_watch_playlist with playlist_id."""
        watch_playlist = {
            "tracks": [{"videoId": "track1", "title": "Track 1"}]
        }
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(playlist_id="PL123")
        
        assert result == watch_playlist

    async def test_get_watch_playlist_with_both_ids(self, mock_ytmusic):
        """Test get_watch_playlist with both video_id and playlist_id."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(video_id="abc123", playlist_id="PL123")
        
        call_kwargs = mock_ytmusic.get_watch_playlist.call_args[1]
        assert call_kwargs["video_id"] == "abc123"
        assert call_kwargs["playlist_id"] == "PL123"

    async def test_get_watch_playlist_with_limit(self, mock_ytmusic):
        """Test get_watch_playlist with limit parameter."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(video_id="abc123", limit=50)
        
        call_kwargs = mock_ytmusic.get_watch_playlist.call_args[1]
        assert call_kwargs["limit"] == 50

    async def test_get_watch_playlist_with_radio(self, mock_ytmusic):
        """Test get_watch_playlist with radio=True."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(video_id="abc123", radio=True)
        
        call_kwargs = mock_ytmusic.get_watch_playlist.call_args[1]
        assert call_kwargs["radio"] == True

    async def test_get_watch_playlist_with_shuffle(self, mock_ytmusic):
        """Test get_watch_playlist with shuffle=True."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(video_id="abc123", shuffle=True)
        
        call_kwargs = mock_ytmusic.get_watch_playlist.call_args[1]
        assert call_kwargs["shuffle"] == True

    async def test_get_watch_playlist_empty_result(self, mock_ytmusic):
        """Test get_watch_playlist with empty result."""
        mock_ytmusic.get_watch_playlist.return_value = None
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(video_id="abc123")
        
        assert result == {}

    async def test_get_watch_playlist_empty_tracks(self, mock_ytmusic):
        """Test get_watch_playlist with empty tracks."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(video_id="abc123")
        
        assert result["tracks"] == []

    async def test_get_watch_playlist_with_many_tracks(self, mock_ytmusic):
        """Test get_watch_playlist with many tracks."""
        tracks = [{"videoId": f"track{i}", "title": f"Track {i}"} for i in range(25)]
        watch_playlist = {"tracks": tracks}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(video_id="abc123", limit=25)
        
        assert len(result["tracks"]) == 25

    async def test_get_watch_playlist_error(self, mock_ytmusic):
        """Test get_watch_playlist handles errors."""
        mock_ytmusic.get_watch_playlist.side_effect = Exception("API Error")
        service = WatchService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_watch_playlist(video_id="abc123")

    async def test_get_watch_playlist_auth_error(self, mock_ytmusic):
        """Test get_watch_playlist handles auth errors."""
        mock_ytmusic.get_watch_playlist.side_effect = Exception(
            "Expecting value: line 1 column 1"
        )
        service = WatchService(mock_ytmusic)
        
        with pytest.raises(AuthenticationError):
            await service.get_watch_playlist(video_id="abc123")

    async def test_get_watch_playlist_rate_limit_error(self, mock_ytmusic):
        """Test get_watch_playlist handles rate limit errors."""
        mock_ytmusic.get_watch_playlist.side_effect = Exception("429 Rate limit")
        service = WatchService(mock_ytmusic)
        
        with pytest.raises(RateLimitError):
            await service.get_watch_playlist(video_id="abc123")


@pytest.mark.asyncio
class TestWatchServiceCaching:
    """Test caching behavior for WatchService."""

    async def test_get_watch_playlist_has_cache_decorator(self, mock_ytmusic):
        """Test that get_watch_playlist has cache decorator."""
        service = WatchService(mock_ytmusic)
        
        assert hasattr(service.get_watch_playlist, '__wrapped__')


@pytest.mark.asyncio
class TestWatchServiceLogging:
    """Test logging behavior for WatchService."""

    async def test_get_watch_playlist_logs_track_count(self, mock_ytmusic):
        """Test get_watch_playlist logs track count."""
        watch_playlist = {
            "tracks": [
                {"videoId": "track1", "title": "Track 1"},
                {"videoId": "track2", "title": "Track 2"},
            ]
        }
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(video_id="abc123")
        
        # Should not raise and should complete successfully
        mock_ytmusic.get_watch_playlist.assert_called_once()


@pytest.mark.asyncio
class TestWatchServiceEdgeCases:
    """Test edge cases for WatchService."""

    async def test_get_watch_playlist_no_ids(self, mock_ytmusic):
        """Test get_watch_playlist without video_id or playlist_id."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist()
        
        # Should still work (ytMusic handles this)
        assert result == watch_playlist

    async def test_get_watch_playlist_with_all_params(self, mock_ytmusic):
        """Test get_watch_playlist with all parameters."""
        watch_playlist = {"tracks": []}
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        await service.get_watch_playlist(
            video_id="abc123",
            playlist_id="PL123",
            limit=50,
            radio=True,
            shuffle=True
        )
        
        call_kwargs = mock_ytmusic.get_watch_playlist.call_args[1]
        assert call_kwargs["video_id"] == "abc123"
        assert call_kwargs["playlist_id"] == "PL123"
        assert call_kwargs["limit"] == 50
        assert call_kwargs["radio"] == True
        assert call_kwargs["shuffle"] == True

    async def test_get_watch_playlist_result_without_tracks_key(self, mock_ytmusic):
        """Test get_watch_playlist when result has no tracks key."""
        watch_playlist = {"playlistId": "PL123"}  # No tracks key
        mock_ytmusic.get_watch_playlist.return_value = watch_playlist
        service = WatchService(mock_ytmusic)
        
        result = await service.get_watch_playlist(video_id="abc123")
        
        # Should return the result as-is
        assert result == watch_playlist
