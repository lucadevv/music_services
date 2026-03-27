"""Tests for podcast endpoints exception passthrough."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import (
    ResourceNotFoundError,
    AuthenticationError,
    RateLimitError,
    ExternalServiceError,
    CircuitBreakerError,
)
from tests.conftest import MockPodcastService
from app.api.v1.endpoints.podcasts import get_podcast_service


@pytest.fixture(autouse=True)
def patch_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
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


SERVICE_EXCEPTIONS = [
    (ResourceNotFoundError("Not found.", {"resource_type": "podcast"}), 404),
    (AuthenticationError("Auth failed.", {"operation": "test"}), 401),
    (RateLimitError("Rate limited.", {"retry_after": 300}), 429),
    (ExternalServiceError("External error.", {"operation": "test"}), 502),
    (CircuitBreakerError("Unavailable.", {"retry_after": 60, "state": "OPEN"}), 503),
]


class TestPodcastChannelEndpoint:

    @pytest.mark.parametrize("exc,expected_status", SERVICE_EXCEPTIONS)
    def test_channel_service_exception_passthrough(self, exc, expected_status):
        mock_service = MockPodcastService()
        mock_service._get_channel_side_effect = exc
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest")
        assert response.status_code == expected_status

    def test_channel_generic_exception_returns_500(self):
        mock_service = MockPodcastService()
        mock_service._get_channel_side_effect = RuntimeError("boom")
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest")
        assert response.status_code == 500

    def test_channel_success_returns_200(self):
        mock_service = MockPodcastService()
        mock_service._get_channel_return = {"title": "Channel"}
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest")
        assert response.status_code == 200


class TestPodcastChannelEpisodesEndpoint:

    @pytest.mark.parametrize("exc,expected_status", SERVICE_EXCEPTIONS)
    def test_channel_episodes_service_exception_passthrough(self, exc, expected_status):
        mock_service = MockPodcastService()
        mock_service._get_channel_episodes_side_effect = exc
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest/episodes")
        assert response.status_code == expected_status

    def test_channel_episodes_generic_exception_returns_500(self):
        mock_service = MockPodcastService()
        mock_service._get_channel_episodes_side_effect = RuntimeError("boom")
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest/episodes")
        assert response.status_code == 500

    def test_channel_episodes_success_returns_200(self):
        mock_service = MockPodcastService()
        mock_service._get_channel_episodes_return = {"episodes": []}
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/channel/UCtest/episodes")
        assert response.status_code == 200


class TestPodcastEndpoint:

    @pytest.mark.parametrize("exc,expected_status", SERVICE_EXCEPTIONS)
    def test_podcast_service_exception_passthrough(self, exc, expected_status):
        mock_service = MockPodcastService()
        mock_service._get_podcast_side_effect = exc
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/MPADtest")
        assert response.status_code == expected_status

    def test_podcast_generic_exception_returns_500(self):
        mock_service = MockPodcastService()
        mock_service._get_podcast_side_effect = RuntimeError("boom")
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/MPADtest")
        assert response.status_code == 500

    def test_podcast_success_returns_200(self):
        mock_service = MockPodcastService()
        mock_service._get_podcast_return = {"title": "Podcast"}
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/MPADtest")
        assert response.status_code == 200


class TestPodcastEpisodeEndpoint:

    @pytest.mark.parametrize("exc,expected_status", SERVICE_EXCEPTIONS)
    def test_episode_service_exception_passthrough(self, exc, expected_status):
        mock_service = MockPodcastService()
        mock_service._get_episode_side_effect = exc
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episode/MPADtest")
        assert response.status_code == expected_status

    def test_episode_generic_exception_returns_500(self):
        mock_service = MockPodcastService()
        mock_service._get_episode_side_effect = RuntimeError("boom")
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episode/MPADtest")
        assert response.status_code == 500

    def test_episode_success_returns_200(self):
        mock_service = MockPodcastService()
        mock_service._get_episode_return = {"title": "Episode"}
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episode/MPADtest")
        assert response.status_code == 200


class TestPodcastEpisodesPlaylistEndpoint:

    @pytest.mark.parametrize("exc,expected_status", SERVICE_EXCEPTIONS)
    def test_episodes_playlist_service_exception_passthrough(self, exc, expected_status):
        mock_service = MockPodcastService()
        mock_service._get_episodes_playlist_side_effect = exc
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episodes/MPADtest/playlist")
        assert response.status_code == expected_status

    def test_episodes_playlist_generic_exception_returns_500(self):
        mock_service = MockPodcastService()
        mock_service._get_episodes_playlist_side_effect = RuntimeError("boom")
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episodes/MPADtest/playlist")
        assert response.status_code == 500

    def test_episodes_playlist_success_returns_200(self):
        mock_service = MockPodcastService()
        mock_service._get_episodes_playlist_return = {"tracks": []}
        app.dependency_overrides[get_podcast_service] = lambda: mock_service
        with TestClient(app) as client:
            response = client.get("/api/v1/podcasts/episodes/MPADtest/playlist")
        assert response.status_code == 200
