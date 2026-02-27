"""YouTube Music client dependency with OAuth authentication."""
from functools import lru_cache
from pathlib import Path
from ytmusicapi import YTMusic, OAuthCredentials
from app.core.config import get_settings


@lru_cache()
def get_ytmusic_client() -> YTMusic:
    """Get cached YTMusic client instance using OAuth authentication."""
    settings = get_settings()
    
    # Rutas de archivos de autenticación
    oauth_path = Path(settings.OAUTH_JSON_PATH)
    browser_path = Path(settings.BROWSER_JSON_PATH)
    client_id = settings.YTMUSIC_CLIENT_ID
    client_secret = settings.YTMUSIC_CLIENT_SECRET
    
    # Intentar browser.json primero (más estable)
    if browser_path.exists():
        try:
            client = YTMusic(str(browser_path))
            print("✅ YTMusic inicializado con browser.json")
            return client
        except Exception as e:
            print(f"⚠️ Browser auth falló: {e}")
    
    # Fallback a OAuth si browser no funciona
    if oauth_path.exists() and client_id and client_secret:
        try:
            credentials = OAuthCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            client = YTMusic(str(oauth_path), oauth_credentials=credentials)
            print("✅ YTMusic inicializado con OAuth")
            return client
        except Exception as e:
            print(f"⚠️ OAuth falló: {e}")
    
    raise FileNotFoundError(
        f"No se encontró archivo de autenticación.\n"
        f"Opciones:\n"
        f"  1. OAuth: Configura YTMUSIC_CLIENT_ID y YTMUSIC_CLIENT_SECRET en .env\n"
        f"     y genera oauth.json con: ytmusicapi oauth\n"
        f"  2. Browser: Crea browser.json siguiendo: "
        f"https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html"
    )


def get_ytmusic() -> YTMusic:
    """Dependency for FastAPI to get YTMusic client."""
    return get_ytmusic_client()
