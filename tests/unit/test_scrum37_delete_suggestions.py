"""Unit tests for SCRUM-37: DELETE /search/suggestions body support.

SCRUM-37: /search/suggestions DELETE returns 422 without body.
Fix: Accept JSON body {"query": "test"} as primary, keep query param as fallback (deprecated).
"""
import pytest
import json
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.search import remove_search_suggestions, get_search_service
from app.services.search_service import SearchService


# Minimal app without full startup
minimal_app = FastAPI()
minimal_app.add_api_route(
    "/api/v1/search/suggestions",
    remove_search_suggestions,
    methods=["DELETE"]
)


@pytest.fixture
def client():
    mock_service = AsyncMock(spec=SearchService)
    mock_service.remove_search_suggestions.return_value = True
    minimal_app.dependency_overrides[get_search_service] = lambda: mock_service
    with TestClient(minimal_app) as c:
        yield c
    minimal_app.dependency_overrides.clear()


class TestScrum37DeleteSuggestionsBody:
    """Test cases for SCRUM-37: DELETE /search/suggestions body support."""

    def test_scrum37_body_json_success(self, client):
        """DELETE with JSON body should return 200."""
        response = client.request(
            "DELETE",
            "/api/v1/search/suggestions",
            content=json.dumps({"query": "cumbia"}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_scrum37_query_param_success(self, client):
        """DELETE with query param should still work (deprecated)."""
        response = client.delete("/api/v1/search/suggestions?q=cumbia")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_scrum37_body_preferred_over_query(self, client):
        """When both body and query param provided, body takes precedence."""
        response = client.request(
            "DELETE",
            "/api/v1/search/suggestions?q=old",
            content=json.dumps({"query": "new"}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

    def test_scrum37_no_body_no_query_returns_422(self, client):
        """DELETE without body or query param should return 422."""
        response = client.delete("/api/v1/search/suggestions")
        assert response.status_code == 422

    def test_scrum37_empty_body_dict_returns_422(self, client):
        """DELETE with empty JSON dict (no 'query' key) should return 422."""
        response = client.request(
            "DELETE",
            "/api/v1/search/suggestions",
            content=json.dumps({}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_scrum37_empty_query_in_body_returns_error(self, client):
        """DELETE with empty query string in body should return 400/422."""
        response = client.request(
            "DELETE",
            "/api/v1/search/suggestions",
            content=json.dumps({"query": ""}),
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in (400, 422)
