"""Integration tests for browse endpoints."""
import pytest
from unittest.mock import patch, MagicMock


class TestBrowseHomeEndpoint:
    """Integration tests for browse home endpoint."""

    def test_get_home_success(self, test_client_with_browse_mocks, sample_home_content):
        """Test successful get home endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_home_return = sample_home_content
        
        response = client.get("/api/v1/browse/home")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_home_empty(self, test_client_with_browse_mocks):
        """Test get home endpoint with empty content."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_home_return = []
        
        response = client.get("/api/v1/browse/home")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_home_error(self, test_client_with_browse_mocks):
        """Test get home endpoint handles errors."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_home_side_effect = Exception("API Error")
        
        response = client.get("/api/v1/browse/home")
        
        assert response.status_code == 500


class TestBrowseArtistEndpoint:
    """Integration tests for browse artist endpoints."""

    def test_get_artist_success(self, test_client_with_browse_mocks, sample_artist):
        """Test successful get artist endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_artist_return = sample_artist
        
        response = client.get("/api/v1/browse/artist/UC123456789")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "description" in data

    def test_get_artist_error(self, test_client_with_browse_mocks):
        """Test get artist endpoint handles errors."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_artist_side_effect = Exception("API Error")
        
        response = client.get("/api/v1/browse/artist/UC123456789")
        
        assert response.status_code == 500

    def test_get_artist_albums_success(self, test_client_with_browse_mocks):
        """Test successful get artist albums endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        albums = {"results": [{"title": "Album 1"}]}
        mock_browse._get_artist_albums_return = albums
        
        response = client.get("/api/v1/browse/artist/UC123456789/albums")
        
        assert response.status_code == 200


class TestBrowseAlbumEndpoint:
    """Integration tests for browse album endpoints."""

    def test_get_album_success(self, test_client_with_browse_mocks, sample_album):
        """Test successful get album endpoint."""
        client, mock_browse, mock_stream = test_client_with_browse_mocks
        mock_browse._get_album_return = sample_album
        mock_stream._enrich_items_with_streams_return = sample_album.get("tracks", [])
        
        response = client.get("/api/v1/browse/album/MPREb123")
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data

    def test_get_album_without_stream_urls(self, test_client_with_browse_mocks, sample_album):
        """Test get album endpoint without stream URLs."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_album_return = sample_album
        
        response = client.get("/api/v1/browse/album/MPREb123?include_stream_urls=false")
        
        assert response.status_code == 200

    def test_get_album_browse_id_success(self, test_client_with_browse_mocks):
        """Test successful get album browse ID endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_album_browse_id_return = "MPREb123"
        
        response = client.get("/api/v1/browse/album/album123/browse-id")
        
        assert response.status_code == 200
        data = response.json()
        assert "browse_id" in data

    def test_get_album_error(self, test_client_with_browse_mocks):
        """Test get album endpoint handles errors."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_album_side_effect = Exception("API Error")
        
        response = client.get("/api/v1/browse/album/MPREb123")
        
        assert response.status_code == 500


class TestBrowseSongEndpoint:
    """Integration tests for browse song endpoints."""

    def test_get_song_success(self, test_client_with_browse_mocks, sample_song):
        """Test successful get song endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_song_return = sample_song
        
        response = client.get("/api/v1/browse/song/abc123xyz")
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data or "videoId" in data

    def test_get_song_related_success(self, test_client_with_browse_mocks):
        """Test successful get song related endpoint."""
        client, mock_browse, mock_stream = test_client_with_browse_mocks
        related = [{"videoId": "rel1", "title": "Related Song"}]
        mock_browse._get_song_related_return = related
        mock_stream._enrich_items_with_streams_return = related
        
        response = client.get("/api/v1/browse/song/abc123xyz/related")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestBrowseLyricsEndpoint:
    """Integration tests for browse lyrics endpoint."""

    def test_get_lyrics_success(self, test_client_with_browse_mocks):
        """Test successful get lyrics endpoint."""
        client, mock_browse, _ = test_client_with_browse_mocks
        lyrics = {"lyrics": "Test lyrics...", "source": "Musixmatch"}
        mock_browse._get_lyrics_return = lyrics
        
        response = client.get("/api/v1/browse/lyrics/MPAD123")
        
        assert response.status_code == 200
        data = response.json()
        assert "lyrics" in data or "source" in data

    def test_get_lyrics_error(self, test_client_with_browse_mocks):
        """Test get lyrics endpoint handles errors."""
        client, mock_browse, _ = test_client_with_browse_mocks
        mock_browse._get_lyrics_side_effect = Exception("API Error")
        
        response = client.get("/api/v1/browse/lyrics/MPAD123")
        
        assert response.status_code == 500
