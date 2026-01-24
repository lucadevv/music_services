"""YouTube Music client dependency."""
from functools import lru_cache
from ytmusicapi import YTMusic
from typing import Optional
from app.core.config import get_settings


@lru_cache()
def get_ytmusic_client() -> YTMusic:
    """Get cached YTMusic client instance."""
    settings = get_settings()
    
    # Try OAuth first, fallback to browser.json
    if settings.OAUTH_JSON_PATH:
        try:
            return YTMusic(settings.OAUTH_JSON_PATH)
        except Exception:
            pass
    
    # Use browser.json as fallback
    return YTMusic(settings.BROWSER_JSON_PATH)


def get_ytmusic() -> YTMusic:
    """Dependency for FastAPI to get YTMusic client."""
    return get_ytmusic_client()
