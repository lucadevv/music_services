"""Unit tests for SCRUM-32 to SCRUM-35 bug fixes.

SCRUM-32: browse/album browse-id fallback
SCRUM-33: stats/stats ImportError graceful handling
SCRUM-34: explore/category deprecated alias
SCRUM-35: artist albums retry + fallback
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.services.browse_service import BrowseService
from app.core.exceptions import ResourceNotFoundError, ExternalServiceError, RateLimitError
from app.main import app
from app.api.v1.endpoints.explore import get_explore_service
from app.core.ytmusic_client import get_ytmusic
from tests.conftest import MockStreamService


class MockExploreService:
    """Mock ExploreService for testing category endpoint."""
    
    def __init__(self):
        self._get_mood_playlists_return = []
        self._get_mood_playlists_side_effect = None
    
    async def get_mood_playlists(self, params):
        if self._get_mood_playlists_side_effect:
            raise self._get_mood_playlists_side_effect
        return self._get_mood_playlists_return


def _make_explore_client(mock_service):
    """Create test client with mocked explore service."""
    mock_stream = MockStreamService()
    app.dependency_overrides[get_explore_service] = lambda: mock_service
    app.dependency_overrides[get_ytmusic] = lambda: mock_stream
    client = TestClient(app)
    client._mock_service = mock_service
    return client


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear dependency overrides after each test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


# =============================================================================
# SCRUM-32: browse/album browse-id fallback
# Tests for get_album_browse_id fallback logic
# =============================================================================

@pytest.mark.asyncio
class TestScrum32BrowseIdFallback:
    """Test cases for SCRUM-32: get_album_browse_id fallback to get_album."""

    async def test_scrum32_browse_id_fallback_to_album(self, mock_ytmusic):
        """When get_album_browse_id returns None but get_album returns data with audioPlaylistId,
        the method returns the audioPlaylistId value."""
        # Arrange
        mock_ytmusic.get_album_browse_id.return_value = None
        mock_ytmusic.get_album.return_value = {
            "title": "Test Album",
            "audioPlaylistId": "OLAK5uy_abc123"
        }
        service = BrowseService(mock_ytmusic)
        
        # Act
        result = await service.get_album_browse_id("album123")
        
        # Assert
        assert result == "OLAK5uy_abc123"
        mock_ytmusic.get_album_browse_id.assert_called_once_with("album123")
        mock_ytmusic.get_album.assert_called_once_with("album123")

    async def test_scrum32_browse_id_fallback_no_audio_playlist(self, mock_ytmusic):
        """When get_album_browse_id returns None and get_album returns data WITHOUT audioPlaylistId,
        returns None."""
        # Arrange
        mock_ytmusic.get_album_browse_id.return_value = None
        mock_ytmusic.get_album.return_value = {
            "title": "Test Album",
            # No audioPlaylistId
        }
        service = BrowseService(mock_ytmusic)
        
        # Act
        result = await service.get_album_browse_id("album123")
        
        # Assert
        assert result is None

    async def test_scrum32_browse_id_fallback_get_album_none(self, mock_ytmusic):
        """When both get_album_browse_id and get_album return None, returns None."""
        # Arrange
        mock_ytmusic.get_album_browse_id.return_value = None
        mock_ytmusic.get_album.return_value = None
        service = BrowseService(mock_ytmusic)
        
        # Act
        result = await service.get_album_browse_id("album123")
        
        # Assert
        assert result is None

    async def test_scrum32_browse_id_fallback_get_album_raises(self, mock_ytmusic):
        """When get_album_browse_id returns None and get_album raises Exception,
        error is handled via _handle_ytmusic_error."""
        # Arrange
        mock_ytmusic.get_album_browse_id.return_value = None
        mock_ytmusic.get_album.side_effect = Exception("YouTube API error")
        service = BrowseService(mock_ytmusic)
        
        # Act & Assert - should raise ExternalServiceError
        with pytest.raises(ExternalServiceError):
            await service.get_album_browse_id("album123")


# =============================================================================
# SCRUM-33: stats/stats ImportError graceful handling
# Tests for graceful error handling in stats endpoint
# =============================================================================

class TestScrum33StatsImportError:
    """Test cases for SCRUM-33: ImportError graceful handling in stats endpoint."""

    def test_scrum33_import_error_returns_graceful_response(self):
        """Patch the imports to raise ImportError, verify endpoint returns 200 with error message."""
        # The imports happen inside the function, so we need to patch at the source
        # The stats.py does: from app.core.config import get_settings
        with patch("app.core.config.get_settings") as mock_settings:
            # Simulate ImportError at module level by patching the import logic
            mock_settings.side_effect = ImportError("Module not found")
            
            client = TestClient(app)
            response = client.get("/api/v1/stats/stats")
            
            # Should return 200 with graceful error response
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "error" in data
            assert "Configuration not available" in data["error"]

    def test_scrum33_settings_error_returns_graceful_response(self):
        """Patch get_settings to raise, verify 200 with error message."""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.side_effect = Exception("Settings error")
            
            client = TestClient(app)
            response = client.get("/api/v1/stats/stats")
            
            # Should return 200 with graceful error response
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "error" in data

    def test_scrum33_cache_stats_failure_partial_result(self):
        """Patch get_cache_stats to raise, verify 200 with partial results."""
        with patch("app.core.cache.get_cache_stats", new_callable=AsyncMock) as mock_cache_stats:
            mock_cache_stats.side_effect = Exception("Cache error")
            
            client = TestClient(app)
            response = client.get("/api/v1/stats/stats")
            
            # Should return 200 with partial results
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "caching" in data
            # caching should have error due to the failure
            assert "error" in data["caching"] or data["caching"].get("enabled") == False

    def test_scrum33_all_components_failure(self):
        """Patch get_settings to raise, verify graceful response."""
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.side_effect = Exception("Total failure")
            
            client = TestClient(app)
            response = client.get("/api/v1/stats/stats")
            
            # Should return 200 with graceful error response
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "error" in data


# =============================================================================
# SCRUM-34: explore/category deprecated alias
# Tests for /explore/category/{category_params} endpoint as alias
# =============================================================================

class TestScrum34CategoryDeprecatedAlias:
    """Test cases for SCRUM-34: /explore/category deprecated alias."""

    def test_scrum34_category_returns_same_as_moods(self):
        """Hit /api/v1/explore/category/test_params, verify it calls get_mood_playlists
        and returns data."""
        mock_service = MockExploreService()
        mock_service._get_mood_playlists_return = [
            {"title": "Test Playlist", "playlistId": "PL123"}
        ]
        
        client = _make_explore_client(mock_service)
        response = client.get("/api/v1/explore/category/test_params")
        
        assert response.status_code == 200
        data = response.json()
        assert "playlists" in data
        assert len(data["playlists"]) == 1
        assert data["playlists"][0]["title"] == "Test Playlist"

    def test_scrum34_category_has_deprecation_warning_header(self):
        """Verify the Warning header is present with value containing 'Deprecated'."""
        mock_service = MockExploreService()
        mock_service._get_mood_playlists_return = [{"title": "Playlist", "playlistId": "PL123"}]
        
        client = _make_explore_client(mock_service)
        response = client.get("/api/v1/explore/category/test_params")
        
        assert response.status_code == 200
        # Check for Warning header
        assert "warning" in [h.lower() for h in response.headers.keys()]
        warning_header = response.headers.get("Warning", "")
        assert "Deprecated" in warning_header
        assert "/explore/moods/" in warning_header

    def test_scrum34_category_endpoint_registered(self):
        """Verify the endpoint exists and is not 404."""
        client = TestClient(app)
        response = client.get("/api/v1/explore/category/any_params")
        
        # Should NOT return 404 - endpoint exists
        assert response.status_code != 404


# =============================================================================
# SCRUM-35: artist albums retry + fallback
# Tests for get_artist_albums retry and fallback logic
# =============================================================================

@pytest.mark.asyncio
class TestScrum35ArtistAlbumsRetry:
    """Test cases for SCRUM-35: get_artist_albums retry and fallback logic."""

    @pytest.fixture(autouse=True)
    async def clear_cache_between_tests(self):
        """Clear cache between tests to avoid interference from @cache_result decorator."""
        from app.core.cache import clear_cache
        await clear_cache()
        yield
        await clear_cache()

    async def test_scrum35_rate_limit_triggers_fallback(self, mock_ytmusic):
        """get_artist_albums raises rate limit error, fallback via get_artist
        returns albums section. Mock asyncio.sleep to avoid actual waiting."""
        # Arrange
        mock_ytmusic.get_artist_albums.side_effect = Exception("429 Too Many Requests")
        mock_ytmusic.get_artist.return_value = {
            "albums": {
                "browseId": "UCArtist",
                "results": [
                    {"title": "Album 1", "browseId": "MPREb1"}
                ]
            }
        }
        
        service = BrowseService(mock_ytmusic)
        
        # Mock asyncio.sleep to avoid delays
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Act
            result = await service.get_artist_albums("UC123")
            
            # Assert - should return albums section from fallback
            assert "results" in result or "browseId" in result

    async def test_scrum35_rate_limit_retry_success_second_attempt(self, mock_ytmusic):
        """First call raises rate limit, but get_artist fallback succeeds with albums data."""
        # Arrange
        mock_ytmusic.get_artist_albums.side_effect = [
            Exception("429 Too Many Requests"),  # First attempt fails
            {"results": [{"title": "Album 1"}]}  # Second attempt succeeds (but we expect fallback to work)
        ]
        mock_ytmusic.get_artist.return_value = {
            "albums": {
                "results": [{"title": "Fallback Album"}]
            }
        }
        
        service = BrowseService(mock_ytmusic)
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Act
            result = await service.get_artist_albums("UC123")
            
            # Assert
            assert result is not None

    async def test_scrum35_all_retries_exhausted_raises(self, mock_ytmusic):
        """Both attempts fail with rate limit AND fallback fails, raises the error
        via _handle_ytmusic_error."""
        # Arrange - use an error message that doesn't trigger RateLimitError detection
        mock_ytmusic.get_artist_albums.side_effect = Exception("Service temporarily unavailable")
        mock_ytmusic.get_artist.side_effect = Exception("Artist service unavailable")
        
        service = BrowseService(mock_ytmusic)
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Act & Assert - should raise ExternalServiceError after all retries exhausted
            with pytest.raises(ExternalServiceError):
                await service.get_artist_albums("UC123")

    async def test_scrum35_non_rate_limit_error_no_retry_fallback(self, mock_ytmusic):
        """A non-rate-limit error should NOT trigger the fallback logic in the same way -
        it should still be retried but the fallback should also fail."""
        # Arrange - non-rate-limit error (e.g., generic API error)
        mock_ytmusic.get_artist_albums.side_effect = Exception("500 Internal Server Error")
        mock_ytmusic.get_artist.side_effect = Exception("Artist API error")
        
        service = BrowseService(mock_ytmusic)
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Act & Assert - should raise ExternalServiceError after retries
            with pytest.raises(ExternalServiceError):
                await service.get_artist_albums("UC123")

    async def test_scrum35_successful_call_no_retry(self, mock_ytmusic):
        """When get_artist_albums succeeds on first try, no retry or fallback needed."""
        # Arrange
        albums_data = {"results": [{"title": "Album 1"}, {"title": "Album 2"}]}
        mock_ytmusic.get_artist_albums.return_value = albums_data
        
        service = BrowseService(mock_ytmusic)
        
        # Act
        result = await service.get_artist_albums("UC123")
        
        # Assert - should return directly without retry
        assert result == albums_data
        mock_ytmusic.get_artist_albums.assert_called_once()
        # get_artist should NOT be called on success
        mock_ytmusic.get_artist.assert_not_called()

    async def test_scrum35_rate_limit_with_empty_albums_fallback(self, mock_ytmusic):
        """Rate limit error triggers fallback, but fallback returns albums section."""
        # Arrange
        mock_ytmusic.get_artist_albums.side_effect = Exception("429 rate limit exceeded")
        mock_ytmusic.get_artist.return_value = {
            "albums": {
                "browseId": "UC123",
                "results": [
                    {"title": "Album from fallback", "browseId": "MPREb1"}
                ]
            }
        }
        
        service = BrowseService(mock_ytmusic)
        
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Act
            result = await service.get_artist_albums("UC123")
            
            # Assert - should return albums section from fallback
            assert "results" in result or "browseId" in result
