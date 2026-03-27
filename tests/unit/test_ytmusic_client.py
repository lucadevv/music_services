"""Unit tests for YTMusic client with OAuth credentials."""
import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.core.ytmusic_client import get_ytmusic_client, reset_ytmusic_client


VALID_CLIENT_ID = "188268615112-test.apps.googleusercontent.com"
VALID_CLIENT_SECRET = "GOCSPX-test-secret"


class TestResetYTMusicClient:

    def test_reset_can_be_called_multiple_times(self):
        reset_ytmusic_client()
        reset_ytmusic_client()
        assert True


class TestGetYTMusicClient:

    def setup_method(self):
        get_ytmusic_client.cache_clear()

    def teardown_method(self):
        get_ytmusic_client.cache_clear()

    def test_raises_when_no_oauth_file(self):
        mock_settings = MagicMock(
            OAUTH_JSON_PATH="oauth.json",
            YTMUSIC_CLIENT_ID=VALID_CLIENT_ID,
            YTMUSIC_CLIENT_SECRET=VALID_CLIENT_SECRET,
        )

        with patch("app.core.ytmusic_client.get_settings", return_value=mock_settings), \
             patch("app.core.ytmusic_client.Path") as mock_path:

            mock_path.return_value.exists.return_value = False

            with pytest.raises(FileNotFoundError, match="oauth.json"):
                get_ytmusic_client()

    def test_raises_when_no_credentials(self):
        mock_settings = MagicMock(
            OAUTH_JSON_PATH="oauth.json",
            YTMUSIC_CLIENT_ID=None,
            YTMUSIC_CLIENT_SECRET=None,
        )

        with patch("app.core.ytmusic_client.get_settings", return_value=mock_settings), \
             patch("app.core.ytmusic_client.Path") as mock_path, \
             patch("app.core.ytmusic_client._get_redis_credentials") as mock_redis:

            mock_path.return_value.exists.return_value = True
            mock_redis.return_value = {}

            with pytest.raises(ValueError, match="No hay credenciales"):
                get_ytmusic_client()

    def test_uses_env_credentials_when_no_redis(self):
        mock_settings = MagicMock(
            OAUTH_JSON_PATH="oauth.json",
            YTMUSIC_CLIENT_ID=VALID_CLIENT_ID,
            YTMUSIC_CLIENT_SECRET=VALID_CLIENT_SECRET,
        )

        with patch("app.core.ytmusic_client.get_settings", return_value=mock_settings), \
             patch("app.core.ytmusic_client.Path") as mock_path, \
             patch("app.core.ytmusic_client._get_redis_credentials") as mock_redis, \
             patch("app.core.ytmusic_client.YTMusic") as mock_ytmusic, \
             patch("app.core.ytmusic_client.OAuthCredentials") as mock_oauth:

            mock_path.return_value.exists.return_value = True
            mock_redis.return_value = {}
            mock_ytmusic.return_value = MagicMock()

            get_ytmusic_client()

            mock_oauth.assert_called_once_with(
                client_id=VALID_CLIENT_ID,
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_uses_redis_credentials_over_env(self):
        mock_settings = MagicMock(
            OAUTH_JSON_PATH="oauth.json",
            YTMUSIC_CLIENT_ID=VALID_CLIENT_ID,
            YTMUSIC_CLIENT_SECRET=VALID_CLIENT_SECRET,
        )

        with patch("app.core.ytmusic_client.get_settings", return_value=mock_settings), \
             patch("app.core.ytmusic_client.Path") as mock_path, \
             patch("app.core.ytmusic_client._get_redis_credentials") as mock_redis, \
             patch("app.core.ytmusic_client.YTMusic") as mock_ytmusic, \
             patch("app.core.ytmusic_client.OAuthCredentials") as mock_oauth:

            mock_path.return_value.exists.return_value = True
            mock_redis.return_value = {
                "client_id": "redis-client-id",
                "client_secret": "redis-client-secret",
            }
            mock_ytmusic.return_value = MagicMock()

            get_ytmusic_client()

            mock_oauth.assert_called_once_with(
                client_id="redis-client-id",
                client_secret="redis-client-secret",
            )

    def test_singleton_behavior(self):
        mock_settings = MagicMock(
            OAUTH_JSON_PATH="oauth.json",
            YTMUSIC_CLIENT_ID=VALID_CLIENT_ID,
            YTMUSIC_CLIENT_SECRET=VALID_CLIENT_SECRET,
        )

        with patch("app.core.ytmusic_client.get_settings", return_value=mock_settings), \
             patch("app.core.ytmusic_client.Path") as mock_path, \
             patch("app.core.ytmusic_client._get_redis_credentials") as mock_redis, \
             patch("app.core.ytmusic_client.YTMusic") as mock_ytmusic, \
             patch("app.core.ytmusic_client.OAuthCredentials"):

            mock_path.return_value.exists.return_value = True
            mock_redis.return_value = {}
            mock_instance = MagicMock()
            mock_ytmusic.return_value = mock_instance

            client1 = get_ytmusic_client()
            client2 = get_ytmusic_client()

            assert client1 is client2
