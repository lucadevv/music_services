"""Tests for watch endpoint exception passthrough."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import (
    ResourceNotFoundError,
    AuthenticationError,
    RateLimitError,
    ExternalServiceError,
    CircuitBreakerError,
    ValidationError,
)
from tests.conftest import MockWatchService, MockStreamService
from app.api.v1.endpoints.watch import get_watch_service, get_stream_service


@pytest.fixture(autouse=True)
def patch_redis():
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
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestWatchEndpointExceptionPassthrough:

    def test_watch_service_exception_404_not_found(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = ResourceNotFoundError(
            message="Video no encontrado.",
            details={"resource_type": "video", "video_id": "invalid"}
        )
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=invalid")
        assert response.status_code == 404

    def test_watch_service_exception_401_auth(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = AuthenticationError(
            message="Error de autenticación.",
            details={"operation": "get_watch_playlist"}
        )
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123")
        assert response.status_code == 401

    def test_watch_service_exception_429_rate_limit(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = RateLimitError(
            message="Rate limit exceeded.",
            details={"retry_after": 300}
        )
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123")
        assert response.status_code == 429

    def test_watch_service_exception_502_external(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = ExternalServiceError(
            message="Error en YouTube Music.",
            details={"operation": "get_watch_playlist"}
        )
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123")
        assert response.status_code == 502

    def test_watch_service_exception_503_circuit_breaker(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = CircuitBreakerError(
            message="Servicio no disponible.",
            details={"retry_after": 60, "state": "OPEN"}
        )
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123")
        assert response.status_code == 503

    def test_watch_generic_exception_returns_500(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_side_effect = RuntimeError("unexpected boom")
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123")
        assert response.status_code == 500

    def test_watch_success_returns_200(self):
        mock_service = MockWatchService()
        mock_service._get_watch_playlist_return = {"tracks": [{"videoId": "abc"}]}
        app.dependency_overrides[get_watch_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/watch/?video_id=abc123&include_stream_urls=false")
        assert response.status_code == 200
