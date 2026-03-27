"""Tests for SCRUM-31: stream endpoint returning redundant fields."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import ResourceNotFoundError, ExternalServiceError
from tests.conftest import MockStreamService
from app.api.v1.endpoints.stream import get_stream_service


def _make_client(mock_service):
    app.dependency_overrides[get_stream_service] = lambda: mock_service
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


class TestSCRUM31_StreamFields:
    def test_stream_url_only_contains_streamurl_field(self):
        """Test that stream endpoint only returns streamUrl field (not url or stream_url)."""
        mock_service = MockStreamService()
        # Set up mock to return a stream URL
        mock_service._get_stream_url_return = {
            "streamUrl": "https://example.com/stream.m4a",
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
            "from_cache": False
        }
        
        client = _make_client(mock_service)
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have streamUrl field
        assert "streamUrl" in data
        assert data["streamUrl"] == "https://example.com/stream.m4a"
        
        # Should NOT have redundant url field
        assert "url" not in data
        
        # Should NOT have redundant stream_url field
        assert "stream_url" not in data
        
        # Should have other expected fields
        assert data["title"] == "Test Song"
        assert data["artist"] == "Test Artist"
        assert data["duration"] == 180
        assert data["thumbnail"] == "https://example.com/thumb.jpg"
        assert data["from_cache"] is False

    def test_stream_url_from_cache_also_correct(self):
        """Test that cached stream URL also only has streamUrl field."""
        mock_service = MockStreamService()
        # Set up mock to return a cached stream URL
        mock_service._get_stream_url_return = {
            "streamUrl": "https://example.com/stream.m4a",
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
            "from_cache": True
        }
        
        client = _make_client(mock_service)
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have streamUrl field
        assert "streamUrl" in data
        assert data["streamUrl"] == "https://example.com/stream.m4a"
        
        # Should NOT have redundant url field
        assert "url" not in data
        
        # Should NOT have redundant stream_url field
        assert "stream_url" not in data
        
        # Should indicate it came from cache
        assert data["from_cache"] is True

    def test_stream_url_handles_errors_correctly(self):
        """Test that error responses don't contain the redundant fields."""
        mock_service = MockStreamService()
        # Set up mock to raise an exception
        mock_service._get_stream_url_side_effect = ExternalServiceError(
            message="No se pudo obtener el stream de audio. Verifica el ID del video.",
            details={"video_id": "dQw4w9WgXcQ", "operation": "get_stream_url"}
        )
        
        client = _make_client(mock_service)
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")
        
        # ExternalServiceError returns 502
        assert response.status_code == 502
        data = response.json()
        
        # Error response should not have the stream fields at all
        assert "streamUrl" not in data
        assert "url" not in data
        assert "stream_url" not in data
        # Check that it's the expected error format
        assert "error" in data
        assert data["error"] is True
        assert "error_code" in data
        assert "message" in data