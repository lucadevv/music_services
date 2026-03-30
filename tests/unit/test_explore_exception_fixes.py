"""Tests for explore endpoints exception handling to verify custom exceptions return correct HTTP status codes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import ResourceNotFoundError, AuthenticationError, ExternalServiceError
from tests.conftest import MockStreamService
from app.api.v1.endpoints.explore import get_explore_service
from app.core.ytmusic_client import get_ytmusic


class MockExploreService:
    """Mock ExploreService for integration tests."""
    
    def __init__(self):
        self._get_home_with_moods_return = {"home": [], "moods": []}
        self._get_charts_return = {"top_songs": [], "trending": []}
        self._get_mood_categories_return = {}
        self._get_mood_playlists_return = []
        
        self._get_home_with_moods_side_effect = None
        self._get_charts_side_effect = None
        self._get_mood_categories_side_effect = None
        self._get_mood_playlists_side_effect = None
    
    async def get_home_with_moods(self):
        if self._get_home_with_moods_side_effect:
            raise self._get_home_with_moods_side_effect
        return self._get_home_with_moods_return
    
    async def get_charts(self, country=None):
        if self._get_charts_side_effect:
            raise self._get_charts_side_effect
        return self._get_charts_return
    
    async def get_mood_categories(self):
        if self._get_mood_categories_side_effect:
            raise self._get_mood_categories_side_effect
        return self._get_mood_categories_return
    
    async def get_mood_playlists(self, params):
        if self._get_mood_playlists_side_effect:
            raise self._get_mood_playlists_side_effect
        return self._get_mood_playlists_return


def _make_client(mock_service):
    """Create test client with mocked explore service."""
    mock_stream = MockStreamService()
    app.dependency_overrides[get_explore_service] = lambda: mock_service
    app.dependency_overrides[get_ytmusic] = lambda: mock_stream
    client = TestClient(app)
    client._mock_service = mock_service
    return client


@pytest.fixture(autouse=True)
def patch_redis():
    """Patch Redis client for all tests."""
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
    """Clear dependency overrides after each test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestExploreEndpointExceptions:
    """Test explore endpoints exception handling."""

    def test_explore_music_resource_not_found_returns_404(self):
        """Test that ResourceNotFoundError in explore endpoint returns 404."""
        mock_service = MockExploreService()
        mock_service._get_home_with_moods_side_effect = ResourceNotFoundError(
            message="Contenido de exploración no encontrado.",
            details={"resource_type": "explore", "operation": "get_home_with_moods"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/")
        assert response.status_code == 404

    def test_explore_music_authentication_error_returns_401(self):
        """Test that AuthenticationError in explore endpoint returns 401."""
        mock_service = MockExploreService()
        mock_service._get_home_with_moods_side_effect = AuthenticationError(
            message="Error de autenticación con YouTube Music.",
            details={"operation": "get_home_with_moods"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/")
        assert response.status_code == 401

    def test_explore_music_external_service_error_returns_502(self):
        """Test that ExternalServiceError in explore endpoint returns 502."""
        mock_service = MockExploreService()
        mock_service._get_home_with_moods_side_effect = ExternalServiceError(
            message="Error en YouTube Music durante get_home_with_moods.",
            details={"operation": "get_home_with_moods", "service": "YouTube Music"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/")
        assert response.status_code == 502

    def test_get_mood_categories_resource_not_found_returns_404(self):
        """Test that ResourceNotFoundError in mood categories endpoint returns 404."""
        mock_service = MockExploreService()
        mock_service._get_mood_categories_side_effect = ResourceNotFoundError(
            message="Categorías de mood no encontradas.",
            details={"resource_type": "mood_categories", "operation": "get_mood_categories"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/moods")
        assert response.status_code == 404

    def test_get_mood_playlists_resource_not_found_returns_404(self):
        """Test that ResourceNotFoundError in mood playlists endpoint returns 404."""
        mock_service = MockExploreService()
        mock_service._get_mood_playlists_side_effect = ResourceNotFoundError(
            message="Playlist de mood no encontrada.",
            details={"resource_type": "mood_playlist", "operation": "get_mood_playlists", "params": "invalid_params"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/moods/invalid_params")
        assert response.status_code == 404

    def test_get_charts_resource_not_found_returns_404(self):
        """Test that ResourceNotFoundError in charts endpoint returns 404."""
        mock_service = MockExploreService()
        mock_service._get_charts_side_effect = ResourceNotFoundError(
            message="Charts no encontrados.",
            details={"resource_type": "charts", "operation": "get_charts"}
        )
        client = _make_client(mock_service)
        response = client.get("/api/v1/explore/charts")
        assert response.status_code == 404