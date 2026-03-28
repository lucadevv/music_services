"""Unit tests for SearchService."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.search_service import SearchService
from app.core.exceptions import RateLimitError, AuthenticationError, ExternalServiceError


@pytest.fixture
def mock_ytmusic():
    """Create a mock YTMusic client."""
    return MagicMock()


@pytest.fixture
def sample_search_results():
    """Sample search results."""
    return [
        {"videoId": "abc123", "title": "Test Song 1"},
        {"videoId": "def456", "title": "Test Song 2"},
    ]


@pytest.mark.asyncio
class TestSearchService:
    """Test cases for SearchService class."""

    async def test_search_success(self, mock_ytmusic, sample_search_results):
        """Test successful search returns paginated results."""
        mock_ytmusic.search.return_value = sample_search_results
        service = SearchService(mock_ytmusic)

        result = await service.search("test query")

        # Now returns dict with items and pagination
        assert "items" in result
        assert "pagination" in result
        assert len(result["items"]) == 2
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

        result = await service.search(
            query="test",
            filter="songs",
            scope="library",
            limit=10,
            ignore_spelling=True
        )

        assert "items" in result

    async def test_search_empty_results(self, mock_ytmusic):
        """Test search with empty results."""
        mock_ytmusic.search.return_value = []
        service = SearchService(mock_ytmusic)

        result = await service.search("nonexistent")

        # Returns dict with empty items and pagination
        assert "items" in result
        assert "pagination" in result
        assert result["items"] == []
        assert result["pagination"]["total_results"] == 0

    async def test_search_none_results(self, mock_ytmusic):
        """Test search with None results."""
        mock_ytmusic.search.return_value = None
        service = SearchService(mock_ytmusic)

        result = await service.search("nonexistent")

        assert "items" in result
        assert result["items"] == []
        assert result["pagination"]["total_results"] == 0

    async def test_search_handles_error(self, mock_ytmusic):
        """Test search handles errors correctly."""
        mock_ytmusic.search.side_effect = Exception("API Error")
        service = SearchService(mock_ytmusic)

        with pytest.raises(Exception):
            await service.search("test query")

    async def test_search_handles_auth_error(self, mock_ytmusic):
        """Test search handles authentication errors."""
        from app.core.exceptions import YTMusicServiceException
        mock_ytmusic.search.side_effect = YTMusicServiceException("Auth failed")
        service = SearchService(mock_ytmusic)

        with pytest.raises(YTMusicServiceException):
            await service.search("test query")

    async def test_search_pagination(self, mock_ytmusic, sample_search_results):
        """Test search pagination parameters."""
        mock_ytmusic.search.return_value = sample_search_results
        service = SearchService(mock_ytmusic)

        result = await service.search("test", page=1, page_size=5)

        assert "pagination" in result
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 5


@pytest.mark.asyncio
class TestSearchSuggestions:
    """Test cases for search suggestions."""

    async def test_get_search_suggestions_success(self, mock_ytmusic):
        """Test successful get search suggestions."""
        mock_ytmusic.get_search_suggestions.return_value = ["suggestion1", "suggestion2"]
        service = SearchService(mock_ytmusic)

        result = await service.get_search_suggestions("test")

        assert result == ["suggestion1", "suggestion2"]
        mock_ytmusic.get_search_suggestions.assert_called_once_with("test")

    async def test_get_search_suggestions_empty(self, mock_ytmusic):
        """Test get search suggestions with empty results."""
        mock_ytmusic.get_search_suggestions.return_value = []
        service = SearchService(mock_ytmusic)

        result = await service.get_search_suggestions("test")

        assert result == []

    async def test_get_search_suggestions_none(self, mock_ytmusic):
        """Test get search suggestions with None results."""
        mock_ytmusic.get_search_suggestions.return_value = None
        service = SearchService(mock_ytmusic)

        result = await service.get_search_suggestions("test")

        assert result == []

    async def test_get_search_suggestions_handles_error(self, mock_ytmusic):
        """Test get search suggestions handles errors."""
        mock_ytmusic.get_search_suggestions.side_effect = Exception("API Error")
        service = SearchService(mock_ytmusic)

        with pytest.raises(Exception):
            await service.get_search_suggestions("test")


@pytest.mark.asyncio
class TestRemoveSearchSuggestions:
    """Test cases for remove search suggestions."""

    async def test_remove_search_suggestions(self, mock_ytmusic):
        """Test remove search suggestion."""
        mock_ytmusic.remove_search_suggestions.return_value = True
        service = SearchService(mock_ytmusic)

        result = await service.remove_search_suggestions("test")

        assert result is True
        mock_ytmusic.remove_search_suggestions.assert_called_once_with("test")
