"""Regression: /browse/song/{video_id}/related uses ytmusicapi correctly.

get_song_related(browseId) requires the ``related`` id from get_watch_playlist(video_id),
not the raw video id. See ytmusicapi BrowsingMixin.get_song_related docstring.
"""
import pytest
from unittest.mock import MagicMock

from app.services.browse_service import BrowseService
from app.core.exceptions import ResourceNotFoundError


@pytest.fixture
def mock_ytmusic():
    mock = MagicMock()
    mock.get_watch_playlist.return_value = {
        "related": "RELATED_TAB_BROWSE_ID",
        "tracks": [],
    }
    mock.get_song_related.return_value = [
        {
            "title": "You might also like",
            "contents": [
                {"videoId": "v1", "title": "One"},
                {"videoId": "v2", "title": "Two"},
            ],
        }
    ]
    return mock


@pytest.mark.asyncio
async def test_related_uses_watch_playlist_browse_id(mock_ytmusic):
    service = BrowseService(mock_ytmusic)
    result = await service.get_song_related("VIDEO_X")

    mock_ytmusic.get_watch_playlist.assert_called_once_with("VIDEO_X")
    mock_ytmusic.get_song_related.assert_called_once_with("RELATED_TAB_BROWSE_ID")
    assert len(result["items"]) == 2
    assert result["items"][0]["videoId"] == "v1"


@pytest.mark.asyncio
async def test_related_no_watch_playlist(mock_ytmusic):
    mock_ytmusic.get_watch_playlist.return_value = None
    service = BrowseService(mock_ytmusic)

    with pytest.raises(ResourceNotFoundError):
        await service.get_song_related("VIDEO_X")
