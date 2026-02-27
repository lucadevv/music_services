"""Integration tests for health and general endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns service info."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "online"
        assert "service" in data
        assert "version" in data
        assert "docs" in data
        assert "api" in data

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestStatsEndpoint:
    """Integration tests for stats endpoint."""

    def test_stats_endpoint(self, test_client):
        """Test stats endpoint returns service statistics."""
        response = test_client.get("/api/v1/stats/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "service" in data
        assert "version" in data
        assert "rate_limiting" in data
        assert "caching" in data
        assert "circuit_breaker" in data
        assert "performance" in data
        
        # Check rate_limiting
        assert "enabled" in data["rate_limiting"]
        
        # Check caching
        assert "enabled" in data["caching"]
        assert "size" in data["caching"]
        
        # Check circuit_breaker
        assert "youtube_stream" in data["circuit_breaker"]
        assert "state" in data["circuit_breaker"]["youtube_stream"]

    def test_stats_endpoint_circuit_breaker_status(self, test_client):
        """Test stats endpoint includes circuit breaker status."""
        response = test_client.get("/api/v1/stats/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        cb = data["circuit_breaker"]["youtube_stream"]
        assert "state" in cb
        assert "failure_count" in cb
        assert "remaining_time_seconds" in cb
        assert "is_blocked" in cb


class TestAPIDocumentation:
    """Integration tests for API documentation endpoints."""

    def test_docs_endpoint(self, test_client):
        """Test Swagger docs endpoint is accessible."""
        response = test_client.get("/docs")
        
        assert response.status_code == 200

    def test_redoc_endpoint(self, test_client):
        """Test ReDoc documentation endpoint is accessible."""
        response = test_client.get("/redoc")
        
        assert response.status_code == 200

    def test_openapi_json(self, test_client):
        """Test OpenAPI JSON schema is accessible."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestProcessTimeHeader:
    """Test X-Process-Time header middleware."""

    def test_process_time_header_present(self, test_client):
        """Test X-Process-Time header is present in responses."""
        response = test_client.get("/")
        
        assert "X-Process-Time" in response.headers
        
        # Should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    def test_process_time_header_on_api_requests(self, test_client):
        """Test X-Process-Time header on API requests."""
        response = test_client.get("/health")
        
        assert "X-Process-Time" in response.headers
