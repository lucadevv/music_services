"""YouTube Music client dependency."""
from functools import lru_cache
from pathlib import Path
from ytmusicapi import YTMusic
from app.core.config import get_settings


@lru_cache()
def get_ytmusic_client() -> YTMusic:
    """Get cached YTMusic client instance using browser authentication."""
    settings = get_settings()
    
    browser_path = Path(settings.BROWSER_JSON_PATH)
    if not browser_path.exists():
        raise FileNotFoundError(
            f"browser.json no encontrado en: {browser_path}\n"
            f"Crea el archivo siguiendo: https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html"
        )
    
    try:
        client = YTMusic(str(browser_path))
        print("✅ YTMusic inicializado con browser.json")
        return client
    except Exception as e:
        error_msg = str(e)
        raise Exception(
            f"Error inicializando YTMusic con browser.json: {error_msg}\n"
            f"Verifica que:\n"
            f"  1. browser.json sea válido y tenga el formato correcto\n"
            f"  2. Los headers de autenticación no estén expirados\n"
            f"  3. La sesión de YouTube Music esté activa en el navegador"
        )


def get_ytmusic() -> YTMusic:
    """Dependency for FastAPI to get YTMusic client."""
    return get_ytmusic_client()
