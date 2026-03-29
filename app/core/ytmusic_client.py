"""YouTube Music client - delegates to browser_client.py for authentication."""
from app.core.browser_client import (
    get_ytmusic as _get_ytmusic,
    is_authenticated as _is_authenticated,
    reset_client_cache as _reset_client_cache,
)


def get_ytmusic():
    """Get YTMusic client with browser authentication.
    
    Delegates to browser_client.py which handles rotation.
    """
    return _get_ytmusic()


def is_authenticated() -> bool:
    """Check if at least one browser account is available."""
    return _is_authenticated()


def reset_ytmusic_client() -> None:
    """Invalidate the cached YTMusic clients to force re-creation."""
    _reset_client_cache()
