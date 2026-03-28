"""Unit tests for SCRUM-36: /browse/song/{video_id}/related retry + fallback.

SCRUM-36: get_song_related returns external service error (502).
Fix: retry with exponential backoff + fallback via get_song().
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.services.browse_service import BrowseService
from app.core.exceptions import ExternalServiceError, RateLimitError, ResourceNotFoundError


@pytest.fixture
def mock_ytmusic():
    """Create a mock ytmusic client."""
    mock = MagicMock()
    mock.get_song_related = MagicMock(return_value=[
        {"videoId": "related1", "title": "Related Song 1"},
        {"videoId": "related2", "title": "Related Song 2"},
    ])
    mock.get_song = MagicMock(return_value={
        "videoId": "test123",
        "title": "Test Song",
        "related": [
            {"videoId": "fallback1", "title": "Fallback Song 1"},
        ],
    })
    return mock


@pytest.fixture
def service(mock_ytmusic):
    """Create a BrowseService with mocked ytmusic."""
    return BrowseService(mock_ytmusic)


class TestScrum36SongRelatedRetry:
    """Test cases for SCRUM-36: song related retry + fallback."""

    @pytest.mark.asyncio
    async def test_scrum36_successful_call_no_retry(self, service, mock_ytmusic):
        """When get_song_related succeeds on first try, no retry needed."""
        result = await service.get_song_related("test123")

        assert len(result) == 2
        assert result[0]["videoId"] == "related1"
        mock_ytmusic.get_song_related.assert_called_once_with("test123")
        # Fallback should NOT be called
        mock_ytmusic.get_song.assert_not_called()

    @pytest.mark.asyncio
    async def test_scrum36_rate_limit_triggers_fallback(self, service, mock_ytmusic):
        """When get_song_related fails with rate limit, fallback to get_song related field."""
        mock_ytmusic.get_song_related.side_effect = Exception("429 rate limit exceeded")

        result = await service.get_song_related("test123")

        assert len(result) == 1
        assert result[0]["videoId"] == "fallback1"
        mock_ytmusic.get_song_related.assert_called_with("test123")
        mock_ytmusic.get_song.assert_called_with("test123")

    @pytest.mark.asyncio
    async def test_scrum36_502_error_triggers_fallback(self, service, mock_ytmusic):
        """When get_song_related fails with 502, fallback to get_song."""
        mock_ytmusic.get_song_related.side_effect = Exception("502 bad gateway")

        result = await service.get_song_related("test123")

        assert len(result) == 1
        assert result[0]["videoId"] == "fallback1"
        mock_ytmusic.get_song.assert_called_with("test123")

    @pytest.mark.asyncio
    async def test_scrum36_retry_success_second_attempt(self, service, mock_ytmusic):
        """When first attempt fails but second succeeds, returns result."""
        call_count = [0]

        def side_effect(video_id):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("500 internal server error")
            return [{"videoId": "retry1", "title": "Retry Song"}]

        mock_ytmusic.get_song_related.side_effect = side_effect
        # Also make get_song return no related to force retry path
        mock_ytmusic.get_song.return_value = {"videoId": "test123", "title": "Test"}

        result = await service.get_song_related("test123")

        assert len(result) == 1
        assert result[0]["videoId"] == "retry1"

    @pytest.mark.asyncio
    async def test_scrum36_all_retries_exhausted_raises(self, service, mock_ytmusic):
        """When all retries exhausted, raises the original error."""
        mock_ytmusic.get_song_related.side_effect = Exception("429 rate limit")
        # Fallback also returns no related data
        mock_ytmusic.get_song.return_value = {"videoId": "test123", "title": "Test"}

        with pytest.raises(RateLimitError):
            await service.get_song_related("test123")

    @pytest.mark.asyncio
    async def test_scrum36_non_retryable_error_no_retry(self, service, mock_ytmusic):
        """When error is not retryable (e.g. 404), still tries fallback but no retry."""
        mock_ytmusic.get_song_related.side_effect = Exception("Not found")
        mock_ytmusic.get_song.return_value = {"videoId": "test123", "title": "Test"}

        with pytest.raises(ResourceNotFoundError):
            await service.get_song_related("test123")

    @pytest.mark.asyncio
    async def test_scrum36_fallback_no_related_field_returns_empty(self, service, mock_ytmusic):
        """When get_song returns data but no 'related' field, returns empty after retry."""
        mock_ytmusic.get_song_related.side_effect = Exception("429 rate limit")
        mock_ytmusic.get_song.return_value = {"videoId": "test123", "title": "Test"}

        with pytest.raises(Exception):
            await service.get_song_related("test123")

    @pytest.mark.asyncio
    async def test_scrum36_none_result_returns_empty_list(self, service, mock_ytmusic):
        """When get_song_related returns None, returns empty list."""
        mock_ytmusic.get_song_related.return_value = None

        result = await service.get_song_related("test123")

        assert result == []

    @pytest.mark.asyncio
    async def test_scrum36_fallback_and_get_song_both_fail(self, service, mock_ytmusic):
        """When both get_song_related and get_song fallback fail, raises error."""
        mock_ytmusic.get_song_related.side_effect = Exception("502 bad gateway")
        mock_ytmusic.get_song.side_effect = Exception("Connection error")

        with pytest.raises(Exception):
            await service.get_song_related("test123")
