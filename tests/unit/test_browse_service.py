"""Unit tests for BrowseService."""
import pytest
from unittest.mock import MagicMock

from app.services.browse_service import BrowseService
from app.core.exceptions import ResourceNotFoundError


@pytest.mark.asyncio
class TestBrowseService:
    """Test cases for BrowseService class."""

    async def test_get_home_success(self, mock_ytmusic, sample_home_content):
        """Test successful get_home returns content."""
        mock_ytmusic.get_home.return_value = sample_home_content
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_home()
        
        assert result == sample_home_content
        mock_ytmusic.get_home.assert_called_once()

    async def test_get_home_empty(self, mock_ytmusic):
        """Test get_home with empty content."""
        mock_ytmusic.get_home.return_value = []
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_home()
        
        assert result == []

    async def test_get_home_none(self, mock_ytmusic):
        """Test get_home when ytmusic returns None."""
        mock_ytmusic.get_home.return_value = None
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_home()
        
        assert result == []

    async def test_get_home_error(self, mock_ytmusic):
        """Test get_home handles errors."""
        mock_ytmusic.get_home.side_effect = Exception("API Error")
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_home()


@pytest.mark.asyncio
class TestGetArtist:
    """Test cases for get_artist method."""

    async def test_get_artist_success(self, mock_ytmusic, sample_artist):
        """Test successful get_artist returns artist data."""
        mock_ytmusic.get_artist.return_value = sample_artist
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_artist("UC123456789")
        
        assert result == sample_artist
        mock_ytmusic.get_artist.assert_called_once_with("UC123456789")

    async def test_get_artist_not_found(self, mock_ytmusic):
        """Test get_artist raises error when artist not found."""
        mock_ytmusic.get_artist.return_value = None
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(ResourceNotFoundError, match="Artista no encontrado"):
            await service.get_artist("invalid_id")

    async def test_get_artist_error(self, mock_ytmusic):
        """Test get_artist handles errors."""
        mock_ytmusic.get_artist.side_effect = Exception("API Error")
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_artist("UC123")


@pytest.mark.asyncio
class TestGetArtistAlbums:
    """Test cases for get_artist_albums method."""

    async def test_get_artist_albums_success(self, mock_ytmusic):
        """Test successful get_artist_albums."""
        albums = {"results": [{"title": "Album 1"}]}
        mock_ytmusic.get_artist_albums.return_value = albums
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_artist_albums("UC123", "params123")
        
        assert result == albums

    async def test_get_artist_albums_none(self, mock_ytmusic):
        """Test get_artist_albums when ytmusic returns None."""
        mock_ytmusic.get_artist_albums.return_value = None
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_artist_albums("UC123")
        
        assert result == {}


@pytest.mark.asyncio
class TestGetAlbum:
    """Test cases for get_album method."""

    async def test_get_album_success(self, mock_ytmusic, sample_album):
        """Test successful get_album returns album data."""
        mock_ytmusic.get_album.return_value = sample_album
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_album("MPREb123")
        
        assert result == sample_album
        mock_ytmusic.get_album.assert_called_once_with("MPREb123")

    async def test_get_album_not_found(self, mock_ytmusic):
        """Test get_album raises error when album not found."""
        mock_ytmusic.get_album.return_value = None
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(ResourceNotFoundError, match="Álbum no encontrado"):
            await service.get_album("invalid_id")

    async def test_get_album_error(self, mock_ytmusic):
        """Test get_album handles errors."""
        mock_ytmusic.get_album.side_effect = Exception("API Error")
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_album("MPREb123")


@pytest.mark.asyncio
class TestGetAlbumBrowseId:
    """Test cases for get_album_browse_id method."""

    async def test_get_album_browse_id_success(self, mock_ytmusic):
        """Test successful get_album_browse_id."""
        mock_ytmusic.get_album_browse_id.return_value = "MPREb123"
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_album_browse_id("album123")
        
        assert result == "MPREb123"

    async def test_get_album_browse_id_none(self, mock_ytmusic):
        """Test get_album_browse_id when returns None."""
        mock_ytmusic.get_album_browse_id.return_value = None
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_album_browse_id("album123")
        
        assert result is None


@pytest.mark.asyncio
class TestGetSong:
    """Test cases for get_song method."""

    async def test_get_song_success(self, mock_ytmusic, sample_song):
        """Test successful get_song returns song data."""
        mock_ytmusic.get_song.return_value = sample_song
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_song("abc123xyz")
        
        assert result == sample_song

    async def test_get_song_with_signature_timestamp(self, mock_ytmusic, sample_song):
        """Test get_song with signature timestamp."""
        mock_ytmusic.get_song.return_value = sample_song
        service = BrowseService(mock_ytmusic)
        
        await service.get_song("abc123xyz", signature_timestamp=12345)
        
        mock_ytmusic.get_song.assert_called_once_with("abc123xyz", 12345)

    async def test_get_song_not_found(self, mock_ytmusic):
        """Test get_song raises error when song not found."""
        mock_ytmusic.get_song.return_value = None
        service = BrowseService(mock_ytmusic)
        
        with pytest.raises(ResourceNotFoundError, match="Canción no encontrada"):
            await service.get_song("invalid_id")


@pytest.mark.asyncio
class TestGetSongRelated:
    """Test cases for get_song_related method."""

    async def test_get_song_related_success(self, mock_ytmusic):
        """Test successful get_song_related."""
        related = [{"videoId": "rel1", "title": "Related Song"}]
        mock_ytmusic.get_song_related.return_value = related
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_song_related("abc123")
        
        assert result == related

    async def test_get_song_related_empty(self, mock_ytmusic):
        """Test get_song_related with no results."""
        mock_ytmusic.get_song_related.return_value = []
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_song_related("abc123")
        
        assert result == []

    async def test_get_song_related_none(self, mock_ytmusic):
        """Test get_song_related when ytmusic returns None."""
        mock_ytmusic.get_song_related.return_value = None
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_song_related("abc123")
        
        assert result == []


@pytest.mark.asyncio
class TestGetLyrics:
    """Test cases for get_lyrics method."""

    async def test_get_lyrics_success(self, mock_ytmusic):
        """Test successful get_lyrics."""
        lyrics = {"lyrics": "Test lyrics...", "source": "Musixmatch"}
        mock_ytmusic.get_lyrics.return_value = lyrics
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_lyrics("MPAD123")
        
        assert result == lyrics

    async def test_get_lyrics_empty(self, mock_ytmusic):
        """Test get_lyrics with no lyrics."""
        mock_ytmusic.get_lyrics.return_value = {}
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_lyrics("MPAD123")
        
        assert result == {}

    async def test_get_lyrics_none(self, mock_ytmusic):
        """Test get_lyrics when ytmusic returns None."""
        mock_ytmusic.get_lyrics.return_value = None
        service = BrowseService(mock_ytmusic)
        
        result = await service.get_lyrics("MPAD123")
        
        assert result == {}


@pytest.mark.asyncio
class TestBrowseServiceCaching:
    """Test caching behavior for BrowseService."""

    async def test_get_home_has_cache_decorator(self, mock_ytmusic):
        """Test that get_home method has cache decorator."""
        service = BrowseService(mock_ytmusic)
        
        assert hasattr(service.get_home, '__wrapped__')

    async def test_get_artist_has_cache_decorator(self, mock_ytmusic):
        """Test that get_artist method has cache decorator."""
        service = BrowseService(mock_ytmusic)
        
        assert hasattr(service.get_artist, '__wrapped__')

    async def test_get_album_has_cache_decorator(self, mock_ytmusic):
        """Test that get_album method has cache decorator."""
        service = BrowseService(mock_ytmusic)
        
        assert hasattr(service.get_album, '__wrapped__')
