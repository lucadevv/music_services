"""Integration tests for stream endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from app.core.exceptions import (
    RateLimitError,
    ExternalServiceError,
    CircuitBreakerError,
)


class TestStreamEndpoint:
    """Integration tests for stream endpoint."""

    def test_get_stream_url_success(self, test_client_with_stream_mocks):
        """Test successful get stream URL endpoint."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_return = {
            "url": "https://example.com/audio.m4a",
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
        }
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"] == "https://example.com/audio.m4a"

    def test_get_stream_url_rate_limited(self, test_client_with_stream_mocks):
        """Test get stream URL when rate limited."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_side_effect = RateLimitError(
            message="Límite de peticiones excedido.",
            details={"retry_after": 300}
        )
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 429
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "RATE_LIMIT_ERROR"

    def test_get_stream_url_circuit_open(self, test_client_with_stream_mocks):
        """Test get stream URL when circuit breaker is open."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_side_effect = CircuitBreakerError(
            message="Servicio temporalmente no disponible.",
            details={"retry_after": 300, "state": "OPEN"}
        )
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 503
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "SERVICE_UNAVAILABLE"

    def test_get_stream_url_external_service_error(self, test_client_with_stream_mocks):
        """Test get stream URL handles external service errors."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_side_effect = ExternalServiceError(
            message="Error obteniendo stream de audio.",
            details={"operation": "get_stream_url"}
        )
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 502

    def test_get_stream_url_no_audio(self, test_client_with_stream_mocks):
        """Test get stream URL when no audio available."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_return = {
            "detail": "yt-dlp no pudo obtener el stream."
        }
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 200
        data = response.json()
        assert "detail" in data

    def test_get_stream_url_invalid_video_id(self, test_client_with_stream_mocks):
        """Test get stream URL with invalid video ID format."""
        client, _ = test_client_with_stream_mocks
        
        response = client.get("/api/v1/stream/short")  # Only 5 characters
        
        assert response.status_code == 400  # ValidationError


class TestStreamEndpointEdgeCases:
    """Test edge cases for stream endpoint."""

    def test_get_stream_url_with_metadata(self, test_client_with_stream_mocks):
        """Test get stream URL includes metadata."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_return = {
            "url": "https://example.com/audio.m4a",
            "title": "Song Title",
            "artist": "Artist Name",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
        }
        
        response = client.get("/api/v1/stream/dQw4w9WgXcQ")  # 11 characters
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Song Title"
        assert data["artist"] == "Artist Name"
        assert data["duration"] == 180
        assert data["thumbnail"] == "https://example.com/thumb.jpg"

    def test_get_stream_url_long_video_id(self, test_client_with_stream_mocks):
        """Test get stream URL with long video ID (should fail validation)."""
        client, mock_stream = test_client_with_stream_mocks
        mock_stream._get_stream_url_return = {
            "url": "https://example.com/audio.m4a",
        }
        
        long_id = "a" * 50
        response = client.get(f"/api/v1/stream/{long_id}")
        
        # Should fail validation because ID is too long
        assert response.status_code == 400
