"""YouTube Music client dependency with OAuth authentication."""
from functools import lru_cache
from pathlib import Path
from ytmusicapi import YTMusic, OAuthCredentials
from app.core.config import get_settings


@lru_cache()
def get_ytmusic_client() -> YTMusic:
    """Get cached YTMusic client instance using OAuth authentication."""
    settings = get_settings()

    oauth_path = Path(settings.OAUTH_JSON_PATH)
    client_id = settings.YTMUSIC_CLIENT_ID
    client_secret = settings.YTMUSIC_CLIENT_SECRET

    if not oauth_path.exists():
        raise FileNotFoundError(
            f"No se encontró archivo de autenticación: {oauth_path}\n"
            f"Genera oauth.json con: ytmusicapi oauth --file oauth.json\n"
            f"Luego configura YTMUSIC_CLIENT_ID y YTMUSIC_CLIENT_SECRET en .env"
        )

    if not client_id or not client_secret:
        raise ValueError(
            "Faltan credenciales OAuth en .env.\n"
            "Configura YTMUSIC_CLIENT_ID y YTMUSIC_CLIENT_SECRET."
        )

    try:
        credentials = OAuthCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        client = YTMusic(str(oauth_path), oauth_credentials=credentials)
        print("✅ YTMusic inicializado con OAuth")
        return client
    except Exception as e:
        raise RuntimeError(
            f"Error inicializando YTMusic con OAuth: {e}\n"
            f"Verifica que oauth.json y las credenciales sean correctas."
        ) from e


def get_ytmusic() -> YTMusic:
    """Dependency for FastAPI to get YTMusic client."""
    return get_ytmusic_client()
