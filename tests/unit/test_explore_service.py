"""Unit tests for ExploreService."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.explore_service import ExploreService


@pytest.mark.asyncio
class TestExploreService:
    """Test cases for ExploreService class."""

    def test_known_genres_constant(self, mock_ytmusic):
        """Test KNOWN_GENRES constant is defined."""
        service = ExploreService(mock_ytmusic)
        
        assert hasattr(service, 'KNOWN_GENRES')
        assert 'ggMPOg1uX3hRRFdlaEhHU09k' in service.KNOWN_GENRES


@pytest.mark.asyncio
class TestGetMoodCategories:
    """Test cases for get_mood_categories method."""

    async def test_get_mood_categories_success(self, mock_ytmusic, sample_mood_categories):
        """Test successful get_mood_categories."""
        mock_ytmusic.get_mood_categories.return_value = sample_mood_categories
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_mood_categories()
        
        assert result == sample_mood_categories

    async def test_get_mood_categories_empty(self, mock_ytmusic):
        """Test get_mood_categories with empty results."""
        mock_ytmusic.get_mood_categories.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_mood_categories()
        
        assert result == {}

    async def test_get_mood_categories_none(self, mock_ytmusic):
        """Test get_mood_categories when ytmusic returns None."""
        mock_ytmusic.get_mood_categories.return_value = None
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_mood_categories()
        
        assert result == {}

    async def test_get_mood_categories_error(self, mock_ytmusic):
        """Test get_mood_categories handles errors."""
        mock_ytmusic.get_mood_categories.side_effect = Exception("API Error")
        service = ExploreService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_mood_categories()


@pytest.mark.asyncio
class TestGetMoodPlaylists:
    """Test cases for get_mood_playlists method."""

    async def test_get_mood_playlists_success(self, mock_ytmusic):
        """Test successful get_mood_playlists."""
        playlists = [{"title": "Playlist 1"}, {"title": "Playlist 2"}]
        mock_ytmusic.get_mood_playlists.return_value = playlists
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_mood_playlists("params123")
        
        assert result == playlists

    async def test_get_mood_playlists_key_error_renderer(self, mock_ytmusic):
        """Test get_mood_playlists handles KeyError with renderer."""
        mock_ytmusic.get_mood_playlists.side_effect = KeyError("musicTwoRowItemRenderer")
        service = ExploreService(mock_ytmusic)
        
        with pytest.raises(Exception, match="parsear"):
            await service.get_mood_playlists("params123")

    async def test_get_mood_playlists_generic_error(self, mock_ytmusic):
        """Test get_mood_playlists handles generic errors."""
        mock_ytmusic.get_mood_playlists.side_effect = Exception("Generic error")
        service = ExploreService(mock_ytmusic)
        
        with pytest.raises(Exception, match="Error obteniendo playlists"):
            await service.get_mood_playlists("params123")


@pytest.mark.asyncio
class TestGetGenreNameFromParams:
    """Test cases for get_genre_name_from_params method."""

    async def test_get_genre_name_from_known_params(self, mock_ytmusic):
        """Test getting genre name from known params."""
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_genre_name_from_params("ggMPOg1uX3hRRFdlaEhHU09k")
        
        assert result == "Cumbia"

    async def test_get_genre_name_from_categories(self, mock_ytmusic, sample_mood_categories):
        """Test getting genre name from mood categories."""
        mock_ytmusic.get_mood_categories.return_value = sample_mood_categories
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_genre_name_from_params("rock1")
        
        assert result == "Rock"

    async def test_get_genre_name_not_found(self, mock_ytmusic, sample_mood_categories):
        """Test getting genre name when not found."""
        mock_ytmusic.get_mood_categories.return_value = sample_mood_categories
        mock_ytmusic.get_home.return_value = []
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_genre_name_from_params("unknown_params")
        
        assert result is None


@pytest.mark.asyncio
class TestFindGenreInStructure:
    """Test cases for _find_genre_in_structure method."""

    def test_find_genre_in_dict(self, mock_ytmusic):
        """Test finding genre in dictionary."""
        service = ExploreService(mock_ytmusic)
        
        data = {"params": "test123", "title": "Test Genre"}
        result = service._find_genre_in_structure(data, "test123")
        
        assert result == "Test Genre"

    def test_find_genre_in_nested_dict(self, mock_ytmusic):
        """Test finding genre in nested dictionary."""
        service = ExploreService(mock_ytmusic)
        
        data = {
            "section1": {
                "items": [
                    {"params": "nested123", "title": "Nested Genre"}
                ]
            }
        }
        result = service._find_genre_in_structure(data, "nested123")
        
        assert result == "Nested Genre"

    def test_find_genre_in_list(self, mock_ytmusic):
        """Test finding genre in list."""
        service = ExploreService(mock_ytmusic)
        
        data = [
            {"params": "list123", "title": "List Genre"},
            {"params": "list456", "title": "Another Genre"},
        ]
        result = service._find_genre_in_structure(data, "list456")
        
        assert result == "Another Genre"

    def test_find_genre_not_found(self, mock_ytmusic):
        """Test finding genre when not present."""
        service = ExploreService(mock_ytmusic)
        
        data = {"params": "other", "title": "Other"}
        result = service._find_genre_in_structure(data, "notfound")
        
        assert result is None


@pytest.mark.asyncio
class TestGetCharts:
    """Test cases for get_charts method."""

    async def test_get_charts_success(self, mock_ytmusic, sample_charts):
        """Test successful get_charts."""
        mock_ytmusic.get_charts.return_value = sample_charts
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_charts()
        
        assert result == sample_charts

    async def test_get_charts_with_country(self, mock_ytmusic):
        """Test get_charts with country parameter."""
        mock_ytmusic.get_charts.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        await service.get_charts(country="US")
        
        mock_ytmusic.get_charts.assert_called_once_with("US")

    async def test_get_charts_empty(self, mock_ytmusic):
        """Test get_charts with empty results."""
        mock_ytmusic.get_charts.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_charts()
        
        assert result == {}

    async def test_get_charts_none(self, mock_ytmusic):
        """Test get_charts when ytmusic returns None."""
        mock_ytmusic.get_charts.return_value = None
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_charts()
        
        assert result == {}


@pytest.mark.asyncio
class TestGetHomeWithMoods:
    """Test cases for get_home_with_moods method."""

    async def test_get_home_with_moods_success(self, mock_ytmusic, sample_home_content):
        """Test successful get_home_with_moods."""
        mock_ytmusic.get_home.return_value = sample_home_content
        mock_ytmusic.get_mood_categories.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_home_with_moods()
        
        assert "home" in result
        assert "moods" in result
        assert result["home"] == sample_home_content

    async def test_get_home_with_moods_extracts_moods(self, mock_ytmusic):
        """Test get_home_with_moods extracts moods section."""
        home_content = [
            {
                "title": "Listen Again",
                "contents": [{"title": "Song 1"}],
            },
            {
                "title": "Moods & Genres",
                "contents": [
                    {"title": "Cumbia", "params": "cumbia123"},
                ],
            },
        ]
        mock_ytmusic.get_home.return_value = home_content
        mock_ytmusic.get_mood_categories.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_home_with_moods()
        
        assert len(result["moods"]) == 1
        assert result["moods"][0]["title"] == "Cumbia"

    async def test_get_home_with_moods_fallback_to_categories(self, mock_ytmusic, sample_mood_categories):
        """Test get_home_with_moods falls back to mood categories."""
        mock_ytmusic.get_home.return_value = []  # No moods in home
        mock_ytmusic.get_mood_categories.return_value = sample_mood_categories
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_home_with_moods()
        
        # Should have moods from categories
        assert len(result["moods"]) > 0

    async def test_get_home_with_moods_empty(self, mock_ytmusic):
        """Test get_home_with_moods with empty home."""
        mock_ytmusic.get_home.return_value = None
        mock_ytmusic.get_mood_categories.return_value = {}
        service = ExploreService(mock_ytmusic)
        
        result = await service.get_home_with_moods()
        
        assert result["home"] == []
        assert result["moods"] == []


@pytest.mark.asyncio
class TestGetMoodPlaylistsAlternative:
    """Test cases for get_mood_playlists_alternative method."""

    @patch("app.services.search_service.SearchService")
    async def test_get_mood_playlists_alternative_success(
        self, mock_search_service_class, mock_ytmusic
    ):
        """Test successful alternative mood playlists search."""
        mock_search_service = MagicMock()
        mock_search_service.search = AsyncMock(return_value=[
            {"playlistId": "pl1", "title": "Playlist 1"},
        ])
        mock_search_service_class.return_value = mock_search_service
        
        service = ExploreService(mock_ytmusic)
        result = await service.get_mood_playlists_alternative("Rock", limit=10)
        
        assert len(result) <= 10

    @patch("app.services.search_service.SearchService")
    async def test_get_mood_playlists_alternative_deduplicates(
        self, mock_search_service_class, mock_ytmusic
    ):
        """Test alternative search deduplicates results."""
        mock_search_service = MagicMock()
        mock_search_service.search = AsyncMock(return_value=[
            {"playlistId": "pl1", "title": "Playlist 1"},
            {"playlistId": "pl1", "title": "Duplicate"},  # Same ID
            {"playlistId": "pl2", "title": "Playlist 2"},
        ])
        mock_search_service_class.return_value = mock_search_service
        
        service = ExploreService(mock_ytmusic)
        result = await service.get_mood_playlists_alternative("Rock")
        
        # Should deduplicate by playlistId
        playlist_ids = [p.get("playlistId") for p in result]
        assert len(playlist_ids) == len(set(playlist_ids))


@pytest.mark.asyncio
class TestExploreServiceCaching:
    """Test caching behavior for ExploreService."""

    async def test_get_mood_categories_has_cache_decorator(self, mock_ytmusic):
        """Test that get_mood_categories has cache decorator."""
        service = ExploreService(mock_ytmusic)
        
        assert hasattr(service.get_mood_categories, '__wrapped__')

    async def test_get_charts_has_cache_decorator(self, mock_ytmusic):
        """Test that get_charts has cache decorator."""
        service = ExploreService(mock_ytmusic)
        
        assert hasattr(service.get_charts, '__wrapped__')

    async def test_get_home_with_moods_has_cache_decorator(self, mock_ytmusic):
        """Test that get_home_with_moods has cache decorator."""
        service = ExploreService(mock_ytmusic)
        
        assert hasattr(service.get_home_with_moods, '__wrapped__')
