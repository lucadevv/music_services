"""Tests for SCRUM-29: /library/, /uploads/, /stats/stats endpoints returning 501 instead of 500."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_library_endpoint_returns_501():
    """Test that /api/v1/library/ returns 501 Not Implemented."""
    client = TestClient(app)
    response = client.get("/api/v1/library/")
    assert response.status_code == 501
    data = response.json()
    assert data["detail"]["error"] == "NOT_IMPLEMENTED"
    assert "Library endpoints are not implemented" in data["detail"]["message"]


def test_uploads_endpoint_returns_501():
    """Test that /api/v1/uploads/ returns 501 Not Implemented."""
    client = TestClient(app)
    response = client.get("/api/v1/uploads/")
    assert response.status_code == 501
    data = response.json()
    assert data["detail"]["error"] == "NOT_IMPLEMENTED"
    assert "Upload endpoints are not implemented" in data["detail"]["message"]


def test_stats_endpoint_returns_200():
    """Test that /api/v1/stats/stats returns 200 OK (it should work correctly)."""
    client = TestClient(app)
    response = client.get("/api/v1/stats/stats")
    # This should return 200 since the stats endpoint has proper error handling
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data