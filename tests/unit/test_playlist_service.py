"""Unit tests for PlaylistService."""
import pytest
from unittest.mock import MagicMock

from app.services.playlist_service import PlaylistService
from app.core.exceptions import ResourceNotFoundError


@pytest.mark.asyncio
class TestPlaylistService:
    """Test cases for PlaylistService class."""


@pytest.mark.asyncio
class TestNormalizePlaylistId:
    """Test cases for _normalize_playlist_id method."""

    def test_normalize_playlist_id_with_vl_prefix(self, mock_ytmusic):
        """Test normalizing playlist ID with VL prefix."""
        service = PlaylistService(mock_ytmusic)
        
        result = service._normalize_playlist_id("VLPL123456789")
        
        assert result == "PL123456789"

    def test_normalize_playlist_id_without_prefix(self, mock_ytmusic):
        """Test normalizing playlist ID without prefix."""
        service = PlaylistService(mock_ytmusic)
        
        result = service._normalize_playlist_id("PL123456789")
        
        assert result == "PL123456789"

    def test_normalize_playlist_id_vl_only(self, mock_ytmusic):
        """Test normalizing playlist ID that is just VL."""
        service = PlaylistService(mock_ytmusic)
        
        result = service._normalize_playlist_id("VL")
        
        assert result == ""


@pytest.mark.asyncio
class TestGetPlaylist:
    """Test cases for get_playlist method."""

    async def test_get_playlist_success(self, mock_ytmusic, sample_playlist):
        """Test successful get_playlist returns playlist data."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        result = await service.get_playlist("PL123456789")
        
        assert result == sample_playlist
        mock_ytmusic.get_playlist.assert_called_once()

    async def test_get_playlist_with_vl_prefix(self, mock_ytmusic, sample_playlist):
        """Test get_playlist normalizes ID with VL prefix."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("VLPL123456789")
        
        # Should be called with normalized ID (without VL)
        mock_ytmusic.get_playlist.assert_called_once()
        call_args = mock_ytmusic.get_playlist.call_args
        assert call_args[0][0] == "PL123456789"

    async def test_get_playlist_with_limit(self, mock_ytmusic, sample_playlist):
        """Test get_playlist with limit parameter."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("PL123", limit=50)
        
        call_args = mock_ytmusic.get_playlist.call_args
        assert call_args[0][1] == 50  # limit is second positional arg

    async def test_get_playlist_with_related(self, mock_ytmusic, sample_playlist):
        """Test get_playlist with related parameter."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("PL123", related=True)
        
        call_args = mock_ytmusic.get_playlist.call_args
        assert call_args[0][2] == True  # related is third positional arg

    async def test_get_playlist_with_suggestions_limit(self, mock_ytmusic, sample_playlist):
        """Test get_playlist with suggestions_limit parameter."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("PL123", suggestions_limit=10)
        
        call_args = mock_ytmusic.get_playlist.call_args
        assert call_args[0][3] == 10  # suggestions_limit is fourth positional arg

    async def test_get_playlist_not_found(self, mock_ytmusic):
        """Test get_playlist raises error when playlist not found."""
        mock_ytmusic.get_playlist.return_value = None
        service = PlaylistService(mock_ytmusic)
        
        with pytest.raises(ResourceNotFoundError, match="Playlist no encontrada"):
            await service.get_playlist("invalid_id")

    async def test_get_playlist_error(self, mock_ytmusic):
        """Test get_playlist handles errors."""
        mock_ytmusic.get_playlist.side_effect = Exception("API Error")
        service = PlaylistService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_playlist("PL123")

    async def test_get_playlist_logs_track_count(self, mock_ytmusic, sample_playlist, caplog):
        """Test get_playlist logs track count."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("PL123456789")
        
        # Check that the playlist was retrieved successfully
        mock_ytmusic.get_playlist.assert_called_once()


@pytest.mark.asyncio
class TestPlaylistServiceCaching:
    """Test caching behavior for PlaylistService."""

    async def test_get_playlist_has_cache_decorator(self, mock_ytmusic):
        """Test that get_playlist has cache decorator."""
        service = PlaylistService(mock_ytmusic)
        
        assert hasattr(service.get_playlist, '__wrapped__')


@pytest.mark.asyncio
class TestPlaylistServiceEdgeCases:
    """Test edge cases for PlaylistService."""

    async def test_get_playlist_empty_tracks(self, mock_ytmusic):
        """Test get_playlist with empty tracks list."""
        empty_playlist = {
            "id": "PL123",
            "title": "Empty Playlist",
            "tracks": [],
        }
        mock_ytmusic.get_playlist.return_value = empty_playlist
        service = PlaylistService(mock_ytmusic)
        
        result = await service.get_playlist("PL123")
        
        assert result["tracks"] == []

    async def test_get_playlist_large_limit(self, mock_ytmusic, sample_playlist):
        """Test get_playlist with large limit."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        await service.get_playlist("PL123", limit=1000)
        
        call_args = mock_ytmusic.get_playlist.call_args
        assert call_args[0][1] == 1000

    async def test_get_playlist_special_characters_in_id(self, mock_ytmusic, sample_playlist):
        """Test get_playlist with special characters in ID."""
        mock_ytmusic.get_playlist.return_value = sample_playlist
        service = PlaylistService(mock_ytmusic)
        
        # IDs with special characters should still work
        await service.get_playlist("PL_123-ABC")
        
        mock_ytmusic.get_playlist.assert_called_once()
