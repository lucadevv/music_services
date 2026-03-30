"""Tests for SCRUM-28: /browse/song/:videoId/related returns 200 empty"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import ResourceNotFoundError, ExternalServiceError
from tests.conftest import MockBrowseService, MockStreamService
from app.api.v1.endpoints.browse import get_browse_service, get_stream_service


def _make_client(mock_service):
    mock_stream = MockStreamService()
    app.dependency_overrides[get_browse_service] = lambda: mock_service
    app.dependency_overrides[get_stream_service] = lambda: mock_stream
    client = TestClient(app)
    client._mock_service = mock_service
    return client


@pytest.fixture(autouse=True)
def patch_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    patches = [
        patch("app.core.cache_redis.get_redis_client", return_value=redis_mock),
        patch("app.core.cache_redis.settings", MagicMock(CACHE_ENABLED=False)),
        patch("app.core.cache_redis._redis_client", redis_mock),
    ]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestSCRUM28_RelatedSongs:
    """Test cases for SCRUM-28: related songs endpoint returning empty data."""

    def test_related_songs_returns_200_with_data_when_available(self):
        """Test that related songs endpoint returns 200 with data when ytmusic returns results."""
        mock_service = MockBrowseService()
        # Mock data that mimics what ytmusicapi.get_song_related might return
        mock_service._get_song_related_return = [
            {
                "videoId": "related1",
                "title": "Related Song 1",
                "thumbnails": [{"url": "https://example.com/thumb1.jpg"}],
                "artists": [{"name": "Artist 1"}],
                "duration": "3:30",
                "views": "1M"
            },
            {
                "videoId": "related2", 
                "title": "Related Song 2",
                "thumbnails": [{"url": "https://example.com/thumb2.jpg"}],
                "artists": [{"name": "Artist 2"}],
                "duration": "4:15",
                "views": "2M"
            }
        ]
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["videoId"] == "related1"
        assert data[0]["title"] == "Related Song 1"
        assert data[1]["videoId"] == "related2"
        assert data[1]["title"] == "Related Song 2"

    def test_related_songs_returns_200_empty_list_when_no_data(self):
        """Test that related songs endpoint returns 200 with empty list when ytmusic returns empty results."""
        mock_service = MockBrowseService()
        mock_service._get_song_related_return = []
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        assert response.status_code == 200
        assert response.json() == []

    def test_related_songs_returns_200_empty_list_when_none_returned(self):
        """Test that related songs endpoint returns 200 with empty list when ytmusic returns None."""
        mock_service = MockBrowseService()
        mock_service._get_song_related_return = None
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        assert response.status_code == 200
        assert response.json() == []

    def test_related_songs_with_stream_urls_enrichment(self):
        """Test that related songs endpoint properly enriches with stream URLs when requested."""
        mock_service = MockBrowseService()
        mock_service._get_song_related_return = [
            {
                "videoId": "related1",
                "title": "Related Song 1",
                "thumbnails": [{"url": "https://example.com/thumb1.jpg"}],
            }
        ]
        
        mock_stream = MockStreamService()
        # Mock the enrichment to return data with stream URLs
        mock_stream._enrich_items_with_streams_return = [
            {
                "videoId": "related1",
                "title": "Related Song 1",
                "thumbnails": [{"url": "https://example.com/thumb1.jpg"}],
                "stream_url": "https://stream.example.com/related1",
                "thumbnail": "https://example.com/bestthumb1.jpg"
            }
        ]
        
        app.dependency_overrides[get_browse_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: mock_stream
        
        with TestClient(app) as client:
            response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=true")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["videoId"] == "related1"
        assert data[0]["title"] == "Related Song 1"
        # Check that stream URL enrichment happened
        assert "stream_url" in data[0]
        assert data[0]["stream_url"] == "https://stream.example.com/related1"
        assert "thumbnail" in data[0]
        assert data[0]["thumbnail"] == "https://example.com/bestthumb1.jpg"
        
        app.dependency_overrides.clear()

    def test_related_songs_handles_youtube_api_exception(self):
        """Test that related songs endpoint handles ytmusic API exceptions properly."""
        mock_service = MockBrowseService()
        mock_service._get_song_related_side_effect = Exception("Internal server error from YouTube")
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        # Should return 502 Bad Gateway for external service errors
        assert response.status_code == 502
        data = response.json()
        assert data.get("error") is True
        assert "error_code" in data
        assert data["error_code"] == "EXTERNAL_SERVICE_ERROR"
        
    def test_related_songs_handles_resource_not_found(self):
        """Test that related songs endpoint handles resource not found properly."""
        mock_service = MockBrowseService()
        mock_service._get_song_related_side_effect = ResourceNotFoundError(
            message="Video not found",
            details={"resource_type": "video", "video_id": "invalid123"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/song/invalid123/related?include_stream_urls=false")
        # Should return 404 for resource not found
        assert response.status_code == 404
        data = response.json()
        assert data.get("error") is True