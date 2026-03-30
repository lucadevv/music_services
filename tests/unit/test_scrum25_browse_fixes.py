"""Tests for SCRUM-25/26/30: browse endpoints returning wrong status codes."""
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


class TestSCRUM25_ArtistEndpoint:

    def test_artist_not_found_returns_404(self):
        mock_service = MockBrowseService()
        mock_service._get_artist_side_effect = ResourceNotFoundError(
            message="Artista no encontrado.",
            details={"resource_type": "artist", "channel_id": "UCinvalid1"}
        )
        app.dependency_overrides[get_browse_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        from app.core.ytmusic_client import get_ytmusic_client
        get_ytmusic_client.cache_clear()
        with TestClient(app) as client:
            response = client.get("/api/v1/browse/artist/UCinvalid1")
        assert response.status_code == 404


class TestSCRUM30_ArtistAlbumsEndpoint:

    def test_artist_albums_not_found_returns_404(self):
        mock_service = MockBrowseService()
        mock_service._get_artist_albums_side_effect = ResourceNotFoundError(
            message="Recurso no encontrado.",
            details={"operation": "obtener álbumes de artista UCinvalid"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/artist/UCinvalid/albums")
        assert response.status_code == 404

    def test_artist_albums_success_returns_200(self):
        mock_service = MockBrowseService()
        mock_service._get_artist_albums_return = {
            "data": [{"browseId": "MPREb_test", "title": "Test Album"}]
        }
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/artist/UCAAA/albums")
        assert response.status_code == 200


class TestSCRUM26_AlbumEndpoint:

    def test_album_not_found_returns_404(self):
        mock_service = MockBrowseService()
        mock_service._get_album_side_effect = ResourceNotFoundError(
            message="Álbum no encontrado.",
            details={"resource_type": "album", "album_id": "MPREb_invalid"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/album/MPREb_invalid?include_stream_urls=false")
        assert response.status_code == 404

    def test_album_success_returns_200(self):
        mock_service = MockBrowseService()
        mock_service._get_album_return = {
            "title": "Test Album",
            "tracks": [{"videoId": "abc123", "title": "Track 1"}]
        }
        client = _make_client(mock_service)
        response = client.get("/api/v1/browse/album/MPREb_test?include_stream_urls=false")
        assert response.status_code == 200
