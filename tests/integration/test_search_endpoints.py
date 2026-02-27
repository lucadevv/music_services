"""Integration tests for search endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from app.core.exceptions import ExternalServiceError


class TestSearchEndpoints:
    """Integration tests for search API endpoints."""

    def test_search_endpoint_success(self, test_client_with_search_mocks, sample_search_results):
        """Test successful search endpoint."""
        client, mock_search, mock_stream = test_client_with_search_mocks
        mock_search._search_return = sample_search_results
        mock_stream._enrich_items_with_streams_return = sample_search_results
        
        response = client.get("/api/v1/search/?q=test query")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "query" in data
        assert data["query"] == "test query"

    def test_search_endpoint_with_filter(self, test_client_with_search_mocks, sample_search_results):
        """Test search endpoint with filter parameter."""
        client, mock_search, mock_stream = test_client_with_search_mocks
        mock_search._search_return = sample_search_results
        mock_stream._enrich_items_with_streams_return = sample_search_results
        
        response = client.get("/api/v1/search/?q=test&filter=songs")
        
        assert response.status_code == 200

    def test_search_endpoint_with_limit(self, test_client_with_search_mocks):
        """Test search endpoint with limit parameter."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._search_return = []
        
        response = client.get("/api/v1/search/?q=test&limit=10")
        
        assert response.status_code == 200

    def test_search_endpoint_missing_query(self, test_client_with_search_mocks):
        """Test search endpoint with missing query parameter."""
        client, _, _ = test_client_with_search_mocks
        
        response = client.get("/api/v1/search/")
        
        assert response.status_code == 422  # Validation error

    def test_search_endpoint_error(self, test_client_with_search_mocks):
        """Test search endpoint handles errors."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._search_side_effect = ExternalServiceError(
            message="Error en YouTube Music durante búsqueda.",
            details={"operation": "search"}
        )
        
        response = client.get("/api/v1/search/?q=test")
        
        assert response.status_code == 502


class TestSearchSuggestionsEndpoints:
    """Integration tests for search suggestions endpoints."""

    def test_get_suggestions_success(self, test_client_with_search_mocks, sample_suggestions):
        """Test successful get search suggestions."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._get_search_suggestions_return = sample_suggestions
        
        response = client.get("/api/v1/search/suggestions?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3

    def test_get_suggestions_empty(self, test_client_with_search_mocks):
        """Test get search suggestions with empty results."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._get_search_suggestions_return = []
        
        response = client.get("/api/v1/search/suggestions?q=nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == []

    def test_remove_suggestions_success(self, test_client_with_search_mocks):
        """Test successful remove search suggestion."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._remove_search_suggestions_return = True
        
        response = client.delete("/api/v1/search/suggestions?q=test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_remove_suggestions_error(self, test_client_with_search_mocks):
        """Test remove search suggestion handles errors."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._remove_search_suggestions_side_effect = ExternalServiceError(
            message="Error en YouTube Music.",
            details={"operation": "remove_search_suggestions"}
        )
        
        response = client.delete("/api/v1/search/suggestions?q=test")
        
        assert response.status_code == 502


class TestSearchEndpointValidation:
    """Test validation for search endpoints."""

    def test_search_limit_validation(self, test_client_with_search_mocks):
        """Test search endpoint validates limit parameter."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._search_return = []
        
        # Limit too high
        response = client.get("/api/v1/search/?q=test&limit=100")
        assert response.status_code == 422
        
        # Limit too low
        response = client.get("/api/v1/search/?q=test&limit=0")
        assert response.status_code == 422

    def test_search_valid_limit(self, test_client_with_search_mocks):
        """Test search endpoint accepts valid limits."""
        client, mock_search, _ = test_client_with_search_mocks
        mock_search._search_return = []
        
        response = client.get("/api/v1/search/?q=test&limit=25")
        assert response.status_code == 200
