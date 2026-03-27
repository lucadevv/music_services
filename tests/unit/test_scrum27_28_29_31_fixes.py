"""Tests for SCRUM-27, SCRUM-28, SCRUM-29, SCRUM-31 bug fixes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import ResourceNotFoundError, ExternalServiceError
from tests.conftest import MockBrowseService, MockStreamService
from app.api.v1.endpoints.browse import get_browse_service, get_stream_service
from app.services.explore_service import ExploreService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def patch_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    patches = [
        patch("app.core.cache_redis.get_redis_client", return_value=redis_mock),
        patch("app.core.cache_redis.settings", MagicMock(CACHE_ENABLED=False)),
        patch("app.core.cache_redis._redis_client", redis_mock),
    ]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


# ============================================================================
# SCRUM-27: /explore/moods/{params} returns 500 on invalid params -> should be 404
# ============================================================================


class TestSCRUM27_MoodPlaylistsInvalidParams:
    """SCRUM-27: /explore/moods/{params} should return 404 when params are invalid."""

    def test_mood_playlists_invalid_params_returns_404(self, mock_ytmusic):
        mock_ytmusic.get_mood_playlists.side_effect = Exception(
            "Server returned HTTP 404: Not Found. Requested entity was not found."
        )
        from app.api.v1.endpoints.explore import get_explore_service

        app.dependency_overrides[get_explore_service] = lambda: ExploreService(mock_ytmusic)
        with TestClient(app) as client:
            response = client.get("/api/v1/explore/moods/happy")
        assert response.status_code == 404
        data = response.json()
        assert data.get("error") is True
        assert "no encontrada" in data.get("message", "").lower() or "not found" in data.get("message", "").lower()

    def test_mood_playlists_valid_params_returns_200(self, mock_ytmusic):
        mock_ytmusic.get_mood_playlists.return_value = [
            {"title": "Cumbia Mix", "playlistId": "PL123"}
        ]
        from app.api.v1.endpoints.explore import get_explore_service

        app.dependency_overrides[get_explore_service] = lambda: ExploreService(mock_ytmusic)
        with TestClient(app) as client:
            response = client.get("/api/v1/explore/moods/ggMPOg1uX3hRRFdlaEhHU09k")
        assert response.status_code == 200
        data = response.json()
        assert "playlists" in data
        assert len(data["playlists"]) == 1

    def test_mood_playlists_generic_error_returns_502(self, mock_ytmusic):
        mock_ytmusic.get_mood_playlists.side_effect = Exception("Internal server error from YouTube")
        from app.api.v1.endpoints.explore import get_explore_service

        app.dependency_overrides[get_explore_service] = lambda: ExploreService(mock_ytmusic)
        with TestClient(app) as client:
            response = client.get("/api/v1/explore/moods/someparams")
        assert response.status_code == 502

    def test_explore_service_mood_playlists_404_raises_resource_not_found(self, mock_ytmusic):
        mock_ytmusic.get_mood_playlists.side_effect = Exception(
            "Server returned HTTP 404: Not Found"
        )
        service = ExploreService(mock_ytmusic)
        with pytest.raises(ResourceNotFoundError):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                service.get_mood_playlists("invalid")
            )

    def test_explore_service_mood_playlists_keyerror_renderer_raises_external(self, mock_ytmusic):
        mock_ytmusic.get_mood_playlists.side_effect = KeyError("musicTwoRowItemRenderer")
        service = ExploreService(mock_ytmusic)
        with pytest.raises(ExternalServiceError):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                service.get_mood_playlists("params123")
            )


# ============================================================================
# SCRUM-28: /browse/song/:videoId/related returns 200 empty
# ============================================================================


class TestSCRUM28_RelatedSongsEmpty:
    """SCRUM-28: /browse/song/:videoId/related should handle empty results gracefully."""

    def test_related_songs_empty_returns_200_empty_list(self):
        mock_service = MockBrowseService()
        mock_service._get_song_related_return = []
        app.dependency_overrides[get_browse_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        assert response.status_code == 200
        assert response.json() == []

    def test_related_songs_with_results_returns_200(self):
        mock_service = MockBrowseService()
        mock_service._get_song_related_return = [
            {"videoId": "related1", "title": "Related Song 1"},
            {"videoId": "related2", "title": "Related Song 2"},
        ]
        app.dependency_overrides[get_browse_service] = lambda: mock_service
        app.dependency_overrides[get_stream_service] = lambda: MockStreamService()
        with TestClient(app) as client:
            response = client.get("/api/v1/browse/song/dQw4w9WgXcQ/related?include_stream_urls=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["videoId"] == "related1"


# ============================================================================
# SCRUM-29: /library/, /uploads/, /stats/stats return 500
# ============================================================================


class TestSCRUM29_LibraryUploadsStats:
    """SCRUM-29: /library/, /uploads/, /stats/stats should return 200."""

    def test_library_root_returns_200(self):
        with TestClient(app) as client:
            response = client.get("/api/v1/library/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "public_endpoints" in data

    def test_uploads_root_returns_200(self):
        with TestClient(app) as client:
            response = client.get("/api/v1/uploads/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "public_endpoints" in data

    def test_stats_returns_200(self):
        with patch("app.core.cache_redis.get_redis_client", return_value=AsyncMock(
            info=AsyncMock(return_value={"used_memory_human": "1MB"}),
            dbsize=AsyncMock(return_value=10),
        )):
            with patch("app.core.cache_redis.settings", MagicMock(CACHE_ENABLED=True)):
                with patch("app.core.cache_redis._redis_client", AsyncMock()):
                    with TestClient(app) as client:
                        response = client.get("/api/v1/stats/stats")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data or "error" in data


# ============================================================================
# SCRUM-31: /stream/:videoId returns redundant fields (url + streamUrl + stream_url)
# ============================================================================


class TestSCRUM31_StreamResponseFields:
    """SCRUM-31: /stream/:videoId should only return streamUrl, not url or stream_url."""

    @patch("app.services.stream_service.yt_dlp")
    def test_stream_response_has_streamUrl_not_url(self, mock_yt_dlp):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180,
            "thumbnail": "https://example.com/thumb.jpg",
            "adaptive_formats": [
                {"acodec": "opus", "vcodec": "none", "url": "https://example.com/audio.m4a"}
            ],
            "formats": [],
        }
        mock_yt_dlp.YoutubeDL.return_value.__enter__.return_value = mock_ydl

        with patch("app.services.stream_service.youtube_stream_circuit") as mock_cb:
            mock_cb.is_open.return_value = False
            mock_cb.get_status.return_value = {
                "state": "closed", "failure_count": 0,
                "remaining_time_seconds": 0, "is_blocked": False,
            }
            mock_cb.record_success.return_value = None

            with patch("app.services.stream_service.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(CACHE_ENABLED=False)
                from app.services.stream_service import StreamService
                StreamService._instance = None
                service = StreamService()
                import asyncio
                result = asyncio.get_event_loop().run_until_complete(
                    service.get_stream_url("dQw4w9WgXcQ")
                )

        assert "streamUrl" in result
        assert "url" not in result
        assert "stream_url" not in result
        assert result["streamUrl"] == "https://example.com/audio.m4a"
        assert result["from_cache"] is False

    def test_stream_response_cached_has_streamUrl_only(self):
        with patch("app.services.stream_service.youtube_stream_circuit") as mock_cb:
            mock_cb.is_open.return_value = False
            mock_cb.get_status.return_value = {
                "state": "closed", "failure_count": 0,
                "remaining_time_seconds": 0, "is_blocked": False,
            }

            with patch("app.services.stream_service.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(CACHE_ENABLED=True)
                with patch("app.services.stream_service.has_cached_key", new_callable=AsyncMock) as mock_has:
                    mock_has.return_value = True
                    with patch("app.services.stream_service.get_cached_value", new_callable=AsyncMock) as mock_get:
                        mock_get.side_effect = [
                            {"title": "Cached Song", "artist": "Artist"},
                            "https://example.com/cached_audio.m4a",
                        ]
                        with patch("app.services.stream_service.get_cached_timestamp", new_callable=AsyncMock) as mock_ts:
                            mock_ts.return_value = 9999999999

                            from app.services.stream_service import StreamService
                            StreamService._instance = None
                            service = StreamService()
                            import asyncio
                            result = asyncio.get_event_loop().run_until_complete(
                                service.get_stream_url("dQw4w9WgXcQ")
                            )

        assert "streamUrl" in result
        assert "url" not in result
        assert "stream_url" not in result
        assert result["from_cache"] is True
