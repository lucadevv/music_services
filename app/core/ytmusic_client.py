"""YouTube Music client dependency with OAuth authentication."""
import json
import logging
from functools import lru_cache
from pathlib import Path

import asyncio

from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth.credentials import OAuthCredentials
from app.core.config import get_settings

logger = logging.getLogger(__name__)

REDIS_CREDENTIALS_KEY = "music:auth:oauth:credentials"


async def _get_redis_credentials() -> dict:
    """Read OAuth credentials from Redis (called from sync context via to_thread)."""
    try:
        import redis.asyncio as redis
        from app.core.cache_redis import _redis_client

        if _redis_client is None:
            from app.core.cache_redis import get_redis_client as _get_client
            _redis_client = await _get_client()

        stored = await _redis_client.get(REDIS_CREDENTIALS_KEY)
        if stored:
            creds = json.loads(stored)
            if creds.get("client_id") and creds.get("client_secret"):
                return creds
    except Exception as e:
        logger.warning(f"Error reading credentials from Redis: {e}")
    return {}


@lru_cache()
def get_ytmusic_client() -> YTMusic:
    """Get cached YTMusic client instance using OAuth authentication.

    Credential priority:
    1. Redis (updated via admin panel)
    2. .env fallback (YTMUSIC_CLIENT_ID / YTMUSIC_CLIENT_SECRET)
    """
    settings = get_settings()
    oauth_path = Path(settings.OAUTH_JSON_PATH)

    # Check if oauth file exists and is valid BEFORE raising error
    oauth_valid = False
    if oauth_path.exists() and oauth_path.stat().st_size > 0:
        try:
            import json
            with open(oauth_path) as f:
                token_data = json.load(f)
            if token_data.get("access_token") and token_data.get("access_token") not in ("", "dummy", None):
                oauth_valid = True
        except Exception:
            pass
    
    if not oauth_valid:
        logger.warning("oauth.json no existe, está vacío o tiene token inválido. API funcionará sin OAuth.")
        return None

    client_id = settings.YTMUSIC_CLIENT_ID
    client_secret = settings.YTMUSIC_CLIENT_SECRET

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                redis_creds = pool.submit(asyncio.run, _get_redis_credentials()).result()
        else:
            redis_creds = asyncio.run(_get_redis_credentials())
    except RuntimeError:
        redis_creds = {}

    if redis_creds:
        client_id = redis_creds["client_id"]
        client_secret = redis_creds["client_secret"]
        logger.info("Using OAuth credentials from Redis")
    elif client_id and client_secret:
        logger.info("Using OAuth credentials from .env")
    else:
        raise ValueError(
            "No hay credenciales OAuth disponibles.\n"
            "Configura client_id y client_secret desde el panel admin o en .env."
        )

    # Check if oauth file is empty or dummy
    oauth_path_obj = Path(oauth_path)
    if not oauth_path_obj.exists() or oauth_path_obj.stat().st_size == 0:
        logger.warning("oauth.json no existe o está vacío. API funcionará sin OAuth.")
        return None
    
    # Check if token is dummy/placeholder
    try:
        import json
        with open(oauth_path) as f:
            token_data = json.load(f)
        if token_data.get("access_token") in ("", "dummy", None):
            logger.warning("oauth.json tiene token inválido. API funcionará sin OAuth.")
            return None
    except Exception:
        pass
    
    try:
        credentials = OAuthCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        client = YTMusic(str(oauth_path), oauth_credentials=credentials)
        print("✅ YTMusic inicializado con OAuth")
        return client
    except Exception as e:
        logger.warning(f"Error inicializando YTMusic con OAuth: {e}. API funcionará sin OAuth.")
        return None


def get_ytmusic() -> YTMusic:
    """Dependency for FastAPI to get YTMusic client."""
    return get_ytmusic_client()


def reset_ytmusic_client() -> None:
    """Invalidate the cached YTMusic client to force re-creation.

    Call this after updating credentials or generating a new token.
    """
    get_ytmusic_client.cache_clear()
    logger.info("YTMusic client cache cleared")
