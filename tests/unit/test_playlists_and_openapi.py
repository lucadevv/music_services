"""Tests for playlists endpoint exception handling fix and /openapi.yaml endpoint."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import (
    ResourceNotFoundError,
    AuthenticationError,
    ExternalServiceError,
    YTMusicServiceException
)
from tests.conftest import MockPlaylistService, MockStreamService
from app.api.v1.endpoints.playlists import get_playlist_service, get_stream_service


@pytest.fixture(autouse=True)
def patch_redis():
    """Mock Redis cache for testing."""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
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


class TestPlaylistsExceptionHandling:
    """Tests for playlists endpoint exception handling fix."""

    def test_playlist_resource_not_found_returns_404(self):
        """Test that ResourceNotFoundError returns 404 (not 500)."""
        mock_service = MockPlaylistService()
        mock_service._get_playlist_side_effect = ResourceNotFoundError(
            message="Playlist no encontrada.",
            details={"resource_type": "playlist", "playlist_id": "PLinvalid"}
        )
        app.dependency_overrides[get_playlist_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        
        with TestClient(app) as client:
            response = client.get("/api/v1/playlists/PLinvalid?include_stream_urls=false")
        
        assert response.status_code == 404

    def test_playlist_authentication_error_returns_401(self):
        """Test that AuthenticationError returns 401 (not 500)."""
        mock_service = MockPlaylistService()
        mock_service._get_playlist_side_effect = AuthenticationError(
            message="Error de autenticación.",
            details={"operation": "get_playlist"}
        )
        app.dependency_overrides[get_playlist_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        
        with TestClient(app) as client:
            response = client.get("/api/v1/playlists/PLtest?include_stream_urls=false")
        
        assert response.status_code == 401

    def test_playlist_external_service_error_returns_502(self):
        """Test that ExternalServiceError returns 502 (not 500)."""
        mock_service = MockPlaylistService()
        mock_service._get_playlist_side_effect = ExternalServiceError(
            message="Error en YouTube Music.",
            details={"operation": "get_playlist"}
        )
        app.dependency_overrides[get_playlist_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        
        with TestClient(app) as client:
            response = client.get("/api/v1/playlists/PLtest?include_stream_urls=false")
        
        assert response.status_code == 502

    def test_playlist_ytservice_exception_in_cache_raises(self):
        """Test that YTMusicServiceException in cache section is re-raised."""
        # This test verifies the fix where YTMusicServiceException in cache section
        # is now properly re-raised instead of being caught by generic Exception
        mock_service = MockPlaylistService()
        mock_service._get_playlist_return = {
            "title": "Test Playlist",
            "tracks": []
        }
        
        app.dependency_overrides[get_playlist_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        
        # Mock the cache to raise YTMusicServiceException
        with patch("app.core.cache_redis.set_cached_value") as mock_set_cache:
            mock_set_cache.side_effect = YTMusicServiceException(
                message="Cache error",
                details={"operation": "set_cached_value"}
            )
            
            with TestClient(app) as client:
                # This should raise the YTMusicServiceException (which gets handled by exception handler)
                response = client.get("/api/v1/playlists/PLtest?include_stream_urls=false")
                
                # Since we're mocking the cache to raise YTMusicServiceException,
                # and the fix re-raises it, it should be handled by the exception handler
                # and return a 500 (since YTMusicServiceException defaults to 500)
                # But actually, let's check what the exception handler does...
                # Looking at the exception handler, it should convert YTMusicServiceException
                # to appropriate status code based on the specific exception type
                
                # For this test, we're mainly verifying that the exception doesn't get
                # swallowed by the generic Exception handler in the cache section
                assert response.status_code == 500  # Default for YTMusicServiceException


class TestOpenAPIYAML:
    """Tests for /openapi.yaml endpoint."""

    def test_openapi_yaml_returns_200(self):
        """Test that GET /openapi.yaml returns 200."""
        with TestClient(app) as client:
            response = client.get("/openapi.yaml")
        
        assert response.status_code == 200

    def test_openapi_yaml_content_type(self):
        """Test that /openapi.yaml returns correct content type."""
        with TestClient(app) as client:
            response = client.get("/openapi.yaml")
        
        assert response.headers["content-type"] == "application/x-yaml"

    def test_openapi_yaml_valid_yaml(self):
        """Test that /openapi.yaml returns valid YAML containing openapi key."""
        with TestClient(app) as client:
            response = client.get("/openapi.yaml")
        
        # Parse YAML
        openapi_spec = yaml.safe_load(response.text)
        
        # Verify it's a dict and contains openapi key
        assert isinstance(openapi_spec, dict)
        assert "openapi" in openapi_spec
        assert openapi_spec["openapi"].startswith("3.")  # Should be OpenAPI 3.x version