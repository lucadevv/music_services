"""Unit tests for OAuth authentication endpoints."""
import json
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from fastapi.testclient import TestClient

from app.main import app

ADMIN_KEY = "test-admin-key-12345"
VALID_CLIENT_ID = "188268615112-test.apps.googleusercontent.com"
VALID_CLIENT_SECRET = "GOCSPX-test-secret"

AUTH_SETTINGS = MagicMock(
    ADMIN_SECRET_KEY=ADMIN_KEY,
    OAUTH_JSON_PATH="oauth.json",
    YTMUSIC_CLIENT_ID=None,
    YTMUSIC_CLIENT_SECRET=None,
)

NO_ADMIN_SETTINGS = MagicMock(
    ADMIN_SECRET_KEY=None,
    OAUTH_JSON_PATH="oauth.json",
    YTMUSIC_CLIENT_ID=None,
    YTMUSIC_CLIENT_SECRET=None,
)

ENV_SETTINGS = MagicMock(
    ADMIN_SECRET_KEY=ADMIN_KEY,
    OAUTH_JSON_PATH="oauth.json",
    YTMUSIC_CLIENT_ID=VALID_CLIENT_ID,
    YTMUSIC_CLIENT_SECRET=VALID_CLIENT_SECRET,
)

STORED_CREDS = json.dumps({
    "client_id": VALID_CLIENT_ID,
    "client_secret": VALID_CLIENT_SECRET,
    "updated_at": "2026-03-27T16:00:00Z",
})

STORED_SESSION = json.dumps({
    "device_code": "test-device-code-123",
    "user_code": "ABCD-EFGH",
    "verification_url": "https://www.google.com/device",
    "expires_in": 900,
    "interval": 5,
    "created_at": time.time(),
})

RAW_TOKEN = {
    "access_token": "ya29.test-token",
    "refresh_token": "1//0dx7-test-refresh",
    "expires_in": 3600,
    "scope": "https://www.googleapis.com/auth/youtube",
    "token_type": "Bearer",
    "refresh_token_expires_in": 7776000,
}

STORED_CREDS_NO_UPDATE = json.dumps({
    "client_id": VALID_CLIENT_ID,
    "client_secret": VALID_CLIENT_SECRET,
})


@pytest.fixture
def mock_redis():
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    return redis_mock


def make_client(mock_redis):
    patches = [
        patch("app.api.v1.endpoints.auth.settings", AUTH_SETTINGS),
        patch("app.core.cache_redis.get_redis_client", return_value=mock_redis),
        patch("app.core.cache_redis.settings", MagicMock(CACHE_ENABLED=False)),
        patch("app.core.cache_redis._redis_client", mock_redis),
    ]
    for p in patches:
        p.start()

    client = TestClient(app)
    client._patches = patches
    yield client

    for p in patches:
        p.stop()


@pytest.fixture
def client(mock_redis):
    yield from make_client(mock_redis)


@pytest.fixture
def auth_headers():
    return {"X-Admin-Key": ADMIN_KEY}


def redis_side_effect(credentials=None, session=None):
    def side_effect(key):
        if "credentials" in key:
            return credentials
        if "session" in key:
            return session
        return None
    return side_effect


# ============================================================================
# POST /api/v1/auth/credentials
# ============================================================================


class TestSaveCredentials:

    def test_save_credentials_success(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/credentials",
            json={"client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_credentials"] is True
        assert data["updated_at"] is not None

    def test_save_credentials_stores_in_redis(self, client, auth_headers, mock_redis):
        client.post(
            "/api/v1/auth/credentials",
            json={"client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET},
            headers=auth_headers,
        )
        mock_redis.set.assert_called_once()
        stored = json.loads(mock_redis.set.call_args[0][1])
        assert stored["client_id"] == VALID_CLIENT_ID
        assert stored["client_secret"] == VALID_CLIENT_SECRET

    def test_save_credentials_resets_ytmusic(self, client, auth_headers, mock_redis):
        with patch("app.api.v1.endpoints.auth.reset_ytmusic_client") as mock_reset:
            client.post(
                "/api/v1/auth/credentials",
                json={"client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET},
                headers=auth_headers,
            )
            mock_reset.assert_called_once()

    def test_save_credentials_missing_client_id(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/credentials",
            json={"client_secret": VALID_CLIENT_SECRET},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_save_credentials_missing_client_secret(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/credentials",
            json={"client_id": VALID_CLIENT_ID},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_save_credentials_client_id_too_short(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/credentials",
            json={"client_id": "short", "client_secret": VALID_CLIENT_SECRET},
            headers=auth_headers,
        )
        assert response.status_code == 422


# ============================================================================
# GET /api/v1/auth/credentials
# ============================================================================


class TestGetCredentials:

    def test_no_credentials(self, client, auth_headers):
        response = client.get("/api/v1/auth/credentials", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["has_credentials"] is False

    def test_with_stored_credentials(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = STORED_CREDS
        response = client.get("/api/v1/auth/credentials", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["has_credentials"] is True
        assert response.json()["updated_at"] == "2026-03-27T16:00:00Z"

    def test_falls_back_to_env(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = None
        with patch("app.api.v1.endpoints.auth.settings", ENV_SETTINGS):
            response = client.get("/api/v1/auth/credentials", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["has_credentials"] is True


# ============================================================================
# POST /api/v1/auth/oauth/start
# ============================================================================


class TestOAuthStart:

    def test_start_success(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(credentials=STORED_CREDS)
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.get_code.return_value = {
                "device_code": "dev-code",
                "user_code": "ABCD-EFGH",
                "verification_url": "https://www.google.com/device",
                "expires_in": 900,
                "interval": 5,
            }
            mock_cls.return_value = mock_instance

            response = client.post("/api/v1/auth/oauth/start", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] is not None
        assert data["user_code"] == "ABCD-EFGH"
        assert data["expires_in"] == 900

    def test_start_stores_session_with_ttl(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(credentials=STORED_CREDS)
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.get_code.return_value = {
                "device_code": "dev-code",
                "user_code": "ABCD-EFGH",
                "verification_url": "https://www.google.com/device",
                "expires_in": 900,
                "interval": 5,
            }
            mock_cls.return_value = mock_instance

            client.post("/api/v1/auth/oauth/start", headers=auth_headers)

        call_kwargs = mock_redis.set.call_args[1]
        assert call_kwargs.get("ex") == 900

    def test_start_no_credentials(self, client, auth_headers, mock_redis):
        response = client.post("/api/v1/auth/oauth/start", headers=auth_headers)
        assert response.status_code == 400

    def test_start_google_error(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(credentials=STORED_CREDS)
        with patch("app.api.v1.endpoints.auth.OAuthCredentials", side_effect=Exception("Connection refused")):
            response = client.post("/api/v1/auth/oauth/start", headers=auth_headers)
        assert response.status_code == 502


# ============================================================================
# POST /api/v1/auth/oauth/poll
# ============================================================================


class TestOAuthPoll:

    def test_pending(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.token_from_code.side_effect = Exception("authorization_pending")
            mock_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_slow_down(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.token_from_code.side_effect = Exception("slow_down")
            mock_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_authorized(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls, \
             patch("builtins.open", mock_open()), \
             patch("app.api.v1.endpoints.auth.reset_ytmusic_client") as mock_reset:

            mock_instance = MagicMock()
            mock_instance.token_from_code.return_value = RAW_TOKEN
            mock_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.json()["status"] == "authorized"
        mock_reset.assert_called_once()
        mock_redis.delete.assert_called_once()

    def test_filters_refresh_token_expires_in(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )

        actual_writes = []

        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls, \
             patch("app.api.v1.endpoints.auth.json.dump") as mock_dump, \
             patch("builtins.open", mock_open()), \
             patch("app.api.v1.endpoints.auth.reset_ytmusic_client"):

            mock_instance = MagicMock()
            mock_instance.token_from_code.return_value = RAW_TOKEN
            mock_cls.return_value = mock_instance

            client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )

        assert mock_dump.called
        written_arg = mock_dump.call_args[0][0]
        assert "refresh_token_expires_in" not in written_arg
        assert written_arg["access_token"] == "ya29.test-token"
        assert "expires_at" in written_arg

    def test_session_not_found(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = None
        response = client.post(
            "/api/v1/auth/oauth/poll",
            json={"session_id": "nonexistent"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_session_expired(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.token_from_code.side_effect = Exception("expired_token")
            mock_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )
        assert response.status_code == 410
        mock_redis.delete.assert_called_once()

    def test_access_denied(self, client, auth_headers, mock_redis):
        mock_redis.get.side_effect = redis_side_effect(
            credentials=STORED_CREDS, session=STORED_SESSION
        )
        with patch("app.api.v1.endpoints.auth.OAuthCredentials") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.token_from_code.side_effect = Exception("access_denied")
            mock_cls.return_value = mock_instance

            response = client.post(
                "/api/v1/auth/oauth/poll",
                json={"session_id": "test-session-id"},
                headers=auth_headers,
            )
        assert response.status_code == 410

    def test_no_credentials(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = STORED_SESSION
        response = client.post(
            "/api/v1/auth/oauth/poll",
            json={"session_id": "test-session-id"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_session_id(self, client, auth_headers):
        response = client.post(
            "/api/v1/auth/oauth/poll", json={}, headers=auth_headers
        )
        assert response.status_code == 422


# ============================================================================
# GET /api/v1/auth/status
# ============================================================================


class TestAuthStatus:

    def test_not_configured(self, client, auth_headers, mock_redis):
        with patch("app.api.v1.endpoints.auth.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            response = client.get("/api/v1/auth/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["has_credentials"] is False
        assert data["has_token"] is False

    def test_credentials_only(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = STORED_CREDS_NO_UPDATE
        with patch("app.api.v1.endpoints.auth.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            response = client.get("/api/v1/auth/status", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["has_credentials"] is True
        assert response.json()["has_token"] is False

    def test_fully_authenticated(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = STORED_CREDS_NO_UPDATE
        mock_ytmusic = MagicMock()
        mock_ytmusic.get_search_suggestions.return_value = ["test"]

        with patch("app.api.v1.endpoints.auth.Path") as mock_path, \
             patch("app.api.v1.endpoints.auth.get_ytmusic_client", return_value=mock_ytmusic):
            mock_path.return_value.exists.return_value = True
            response = client.get("/api/v1/auth/status", headers=auth_headers)

        data = response.json()
        assert data["authenticated"] is True
        assert data["has_token"] is True

    def test_auth_fails(self, client, auth_headers, mock_redis):
        mock_redis.get.return_value = STORED_CREDS_NO_UPDATE
        mock_ytmusic = MagicMock()
        mock_ytmusic.get_search_suggestions.side_effect = Exception("Auth failed")

        with patch("app.api.v1.endpoints.auth.Path") as mock_path, \
             patch("app.api.v1.endpoints.auth.get_ytmusic_client", return_value=mock_ytmusic):
            mock_path.return_value.exists.return_value = True
            response = client.get("/api/v1/auth/status", headers=auth_headers)

        assert response.json()["authenticated"] is False
        assert response.json()["has_token"] is True


# ============================================================================
# Admin Key Verification
# ============================================================================


class TestAdminKeyVerification:

    def test_no_header(self, client):
        response = client.post("/api/v1/auth/credentials", json={
            "client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET,
        })
        assert response.status_code == 403

    def test_wrong_key(self, client):
        response = client.post(
            "/api/v1/auth/credentials",
            json={"client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET},
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert response.status_code == 403

    def test_no_secret_configured(self, mock_redis):
        patches = [
            patch("app.api.v1.endpoints.auth.settings", NO_ADMIN_SETTINGS),
            patch("app.core.cache_redis.get_redis_client", return_value=mock_redis),
            patch("app.core.cache_redis.settings", MagicMock(CACHE_ENABLED=False)),
            patch("app.core.cache_redis._redis_client", mock_redis),
        ]
        for p in patches:
            p.start()
        try:
            c = TestClient(app)
            response = c.post(
                "/api/v1/auth/credentials",
                json={"client_id": VALID_CLIENT_ID, "client_secret": VALID_CLIENT_SECRET},
                headers={"X-Admin-Key": "any-key"},
            )
        finally:
            for p in patches:
                p.stop()
        assert response.status_code == 403
        assert "ADMIN_SECRET_KEY" in response.json()["detail"]
