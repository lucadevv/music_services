"""Unit tests for SearchService."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.search_service import SearchService
from app.core.exceptions import RateLimitError, AuthenticationError, ExternalServiceError


@pytest.mark.asyncio
class TestSearchService:
    """Test cases for SearchService class."""

    async def test_search_success(self, mock_ytmusic, sample_search_results):
        """Test successful search returns results."""
        mock_ytmusic.search.return_value = sample_search_results
        service = SearchService(mock_ytmusic)
        
        result = await service.search("test query")
        
        assert result == sample_search_results
        mock_ytmusic.search.assert_called_once()

    async def test_search_with_filter(self, mock_ytmusic, sample_search_results):
        """Test search with filter parameter."""
        mock_ytmusic.search.return_value = sample_search_results
        service = SearchService(mock_ytmusic)
        
        await service.search("test query", filter="songs")
        
        mock_ytmusic.search.assert_called_once_with(
            query="test query",
            filter="songs",
            scope=None,
            limit=20,
            ignore_spelling=False
        )

    async def test_search_with_all_params(self, mock_ytmusic, sample_search_results):
        """Test search with all parameters."""
        mock_ytmusic.search.return_value = sample_search_results
        service = SearchService(mock_ytmusic)
        
        await service.search(
            query="test",
            filter="songs",
            scope="library",
            limit=10,
            ignore_spelling=True
        )
        
        mock_ytmusic.search.assert_called_once_with(
            query="test",
            filter="songs",
            scope="library",
            limit=10,
            ignore_spelling=True
        )

    async def test_search_empty_results(self, mock_ytmusic):
        """Test search with no results returns empty list."""
        mock_ytmusic.search.return_value = []
        service = SearchService(mock_ytmusic)
        
        result = await service.search("nonexistent song")
        
        assert result == []

    async def test_search_none_results(self, mock_ytmusic):
        """Test search when ytmusic returns None."""
        mock_ytmusic.search.return_value = None
        service = SearchService(mock_ytmusic)
        
        result = await service.search("test")
        
        assert result == []

    async def test_search_unexpected_response_type(self, mock_ytmusic):
        """Test search raises error for unexpected response type."""
        mock_ytmusic.search.return_value = {"not": "a list"}
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(ExternalServiceError):
            await service.search("test")

    async def test_search_handles_ytmusic_error(self, mock_ytmusic):
        """Test search handles ytmusicapi errors."""
        mock_ytmusic.search.side_effect = Exception("API Error")
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(ExternalServiceError):
            await service.search("test")

    async def test_search_handles_rate_limit_error(self, mock_ytmusic):
        """Test search handles rate limit errors."""
        mock_ytmusic.search.side_effect = Exception("429 Rate limit")
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(RateLimitError):
            await service.search("test")

    async def test_search_handles_auth_error(self, mock_ytmusic):
        """Test search handles authentication errors."""
        mock_ytmusic.search.side_effect = Exception("Expecting value: line 1 column 1")
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(AuthenticationError):
            await service.search("test")


@pytest.mark.asyncio
class TestSearchSuggestions:
    """Test cases for search suggestions."""

    async def test_get_search_suggestions_success(self, mock_ytmusic, sample_suggestions):
        """Test successful get search suggestions."""
        mock_ytmusic.get_search_suggestions.return_value = sample_suggestions
        service = SearchService(mock_ytmusic)
        
        result = await service.get_search_suggestions("test")
        
        assert result == sample_suggestions
        mock_ytmusic.get_search_suggestions.assert_called_once_with("test")

    async def test_get_search_suggestions_empty(self, mock_ytmusic):
        """Test get search suggestions with no results."""
        mock_ytmusic.get_search_suggestions.return_value = []
        service = SearchService(mock_ytmusic)
        
        result = await service.get_search_suggestions("xyznonexistent")
        
        assert result == []

    async def test_get_search_suggestions_none(self, mock_ytmusic):
        """Test get search suggestions when ytmusic returns None."""
        mock_ytmusic.get_search_suggestions.return_value = None
        service = SearchService(mock_ytmusic)
        
        result = await service.get_search_suggestions("test")
        
        assert result == []

    async def test_get_search_suggestions_error(self, mock_ytmusic):
        """Test get search suggestions handles errors."""
        mock_ytmusic.get_search_suggestions.side_effect = Exception("Error")
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_search_suggestions("test")


@pytest.mark.asyncio
class TestRemoveSearchSuggestions:
    """Test cases for removing search suggestions."""

    async def test_remove_search_suggestions_success(self, mock_ytmusic):
        """Test successful remove search suggestion."""
        mock_ytmusic.remove_search_suggestions.return_value = True
        service = SearchService(mock_ytmusic)
        
        result = await service.remove_search_suggestions("test query")
        
        assert result is True
        mock_ytmusic.remove_search_suggestions.assert_called_once_with("test query")

    async def test_remove_search_suggestions_returns_false(self, mock_ytmusic):
        """Test remove search suggestion returns False."""
        mock_ytmusic.remove_search_suggestions.return_value = False
        service = SearchService(mock_ytmusic)
        
        result = await service.remove_search_suggestions("nonexistent")
        
        assert result is False

    async def test_remove_search_suggestions_error(self, mock_ytmusic):
        """Test remove search suggestion handles errors."""
        mock_ytmusic.remove_search_suggestions.side_effect = Exception("Error")
        service = SearchService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.remove_search_suggestions("test")


@pytest.mark.asyncio
class TestSearchServiceCaching:
    """Test caching behavior for SearchService."""

    @patch("app.services.search_service.cache_result")
    async def test_search_has_cache_decorator(self, mock_cache, mock_ytmusic):
        """Test that search method has cache decorator."""
        # The cache_result decorator should be applied
        # We verify by checking the method exists
        service = SearchService(mock_ytmusic)
        
        assert hasattr(service.search, '__wrapped__')

    @patch("app.services.search_service.cache_result")
    async def test_get_suggestions_has_cache_decorator(self, mock_cache, mock_ytmusic):
        """Test that get_search_suggestions has cache decorator."""
        service = SearchService(mock_ytmusic)
        
        assert hasattr(service.get_search_suggestions, '__wrapped__')
