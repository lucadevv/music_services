"""OAuth authentication endpoints for admin panel."""
import json
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from ytmusicapi.auth.oauth.credentials import OAuthCredentials

from app.core.config import get_settings
from app.core.cache_redis import get_redis_client
from app.core.ytmusic_client import get_ytmusic_client, reset_ytmusic_client
from app.schemas.auth import (
    CredentialsRequest,
    CredentialsResponse,
    OAuthStartResponse,
    OAuthPollRequest,
    OAuthPollPendingResponse,
    OAuthPollAuthorizedResponse,
    AuthStatusResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

REDIS_CREDENTIALS_KEY = "music:auth:oauth:credentials"
REDIS_SESSION_PREFIX = "music:auth:oauth:session:"

EXPECTED_TOKEN_FIELDS = {
    "access_token",
    "refresh_token",
    "expires_in",
    "scope",
    "token_type",
}

FORBIDDEN_RESPONSE = {
    403: {
        "description": "Admin key inválida o no configurada",
        "content": {
            "application/json": {
                "example": {"detail": "Admin key inválida."}
            }
        },
    }
}

NO_CREDENTIALS_RESPONSE = {
    400: {
        "description": "No hay credenciales OAuth configuradas",
        "content": {
            "application/json": {
                "example": {
                    "detail": "No hay credenciales OAuth configuradas. Guarda client_id y client_secret primero."
                }
            }
        },
    }
}

SESSION_NOT_FOUND_RESPONSE = {
    404: {
        "description": "Sesión no encontrada o expirada",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Sesión no encontrada o expirada. Inicia un nuevo flujo OAuth."
                }
            }
        },
    }
}

SESSION_EXPIRED_RESPONSE = {
    410: {
        "description": "Sesión expirada o denegada por el usuario",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Sesión expirada o denegada. Inicia un nuevo flujo OAuth."
                }
            }
        },
    }
}

GOOGLE_ERROR_RESPONSE = {
    502: {
        "description": "Error comunicándose con Google OAuth",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error comunicándose con Google OAuth: ..."
                }
            }
        },
    }
}


async def verify_admin_key(
    x_admin_key: Optional[str] = Header(
        None,
        alias="X-Admin-Key",
        description="Clave secreta de administrador (configurada en .env como ADMIN_SECRET_KEY)",
        examples=["mi-clave-super-secreta"],
    ),
) -> None:
    """Verify the admin key from request header.

    ADMIN_SECRET_KEY is mandatory. If not configured, all auth endpoints return 403.
    """
    configured_key = settings.ADMIN_SECRET_KEY
    if not configured_key:
        raise HTTPException(
            status_code=403,
            detail="ADMIN_SECRET_KEY no configurado. Configuralo en .env.",
        )
    if not x_admin_key or x_admin_key != configured_key:
        raise HTTPException(
            status_code=403,
            detail="Admin key inválida.",
        )


async def get_oauth_credentials() -> Dict[str, str]:
    """Get OAuth credentials from Redis, fallback to .env."""
    try:
        client = await get_redis_client()
        stored = await client.get(REDIS_CREDENTIALS_KEY)
        if stored:
            creds = json.loads(stored)
            if creds.get("client_id") and creds.get("client_secret"):
                return creds
    except Exception as e:
        logger.warning(f"Error reading credentials from Redis: {e}")

    if settings.YTMUSIC_CLIENT_ID and settings.YTMUSIC_CLIENT_SECRET:
        return {
            "client_id": settings.YTMUSIC_CLIENT_ID,
            "client_secret": settings.YTMUSIC_CLIENT_SECRET,
        }

    return {}


@router.post(
    "/credentials",
    response_model=CredentialsResponse,
    summary="Guardar credenciales OAuth",
    description="""
Guarda el Client ID y Client Secret de Google Cloud en Redis.

Estas credenciales se usan para iniciar el flujo OAuth y para refrescar tokens.
Se guardan en Redis (no en .env), por lo que se pueden actualizar desde el panel
admin sin reiniciar el servicio.

**Requisitos previos:**
- Haber creado un OAuth Client ID en Google Cloud Console
- Application type: "TVs and Limited Input Devices"
- YouTube Data API v3 habilitada
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Credenciales guardadas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "has_credentials": True,
                        "updated_at": "2026-03-27T16:00:00Z",
                    }
                }
            },
        },
    },
)
async def save_credentials(
    body: CredentialsRequest,
    _verified: None = Depends(verify_admin_key),
):
    client = await get_redis_client()
    data = {
        "client_id": body.client_id,
        "client_secret": body.client_secret,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    await client.set(REDIS_CREDENTIALS_KEY, json.dumps(data))
    logger.info("OAuth credentials saved to Redis")
    reset_ytmusic_client()
    return CredentialsResponse(
        has_credentials=True,
        updated_at=data["updated_at"],
    )


@router.get(
    "/credentials",
    response_model=CredentialsResponse,
    summary="Consultar estado de credenciales",
    description="""
Verifica si hay credenciales OAuth almacenadas en Redis (o en .env como fallback).
No expone los valores de client_id ni client_secret por seguridad.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Estado de credenciales",
            "content": {
                "application/json": {
                    "example": {
                        "has_credentials": True,
                        "updated_at": "2026-03-27T16:00:00Z",
                    }
                }
            },
        },
    },
)
async def get_credentials(
    _verified: None = Depends(verify_admin_key),
):
    creds = await get_oauth_credentials()
    return CredentialsResponse(
        has_credentials=bool(creds),
        updated_at=creds.get("updated_at"),
    )


@router.post(
    "/oauth/start",
    response_model=OAuthStartResponse,
    summary="Iniciar flujo OAuth",
    description="""
Inicia el flujo de autorización OAuth Device Flow de Google.

**Flujo:**
1. Se solicita un código de dispositivo a Google
2. Google devuelve una URL de verificación y un código de usuario
3. El usuario debe abrir la URL e ingresar el código
4. Se crea una sesión en Redis para hacer polling

**Importante:** La sesión expira en ~15 minutos. Si el usuario no autoriza a tiempo,
debes iniciar un nuevo flujo.

**Después de este endpoint:**
- Muestra al usuario la `verification_url` y el `user_code`
- Llama a `POST /auth/oauth/poll` con el `session_id` cada 5 segundos
""",
    responses={
        **FORBIDDEN_RESPONSE,
        **NO_CREDENTIALS_RESPONSE,
        **GOOGLE_ERROR_RESPONSE,
        200: {
            "description": "Flujo OAuth iniciado",
            "content": {
                "application/json": {
                    "example": {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "verification_url": "https://www.google.com/device",
                        "user_code": "ABCD-EFGH",
                        "expires_in": 900,
                        "interval": 5,
                    }
                }
            },
        },
    },
)
async def start_oauth_flow(
    _verified: None = Depends(verify_admin_key),
):
    creds = await get_oauth_credentials()
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="No hay credenciales OAuth configuradas. Guarda client_id y client_secret primero.",
        )

    try:
        oauth_creds = OAuthCredentials(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
        code_response = oauth_creds.get_code()

        session_id = str(uuid.uuid4())
        session_data = {
            "device_code": code_response["device_code"],
            "user_code": code_response["user_code"],
            "verification_url": code_response["verification_url"],
            "expires_in": code_response["expires_in"],
            "interval": code_response.get("interval", 5),
            "created_at": time.time(),
        }

        client = await get_redis_client()
        await client.set(
            f"{REDIS_SESSION_PREFIX}{session_id}",
            json.dumps(session_data),
            ex=session_data["expires_in"],
        )

        logger.info(f"OAuth session started: {session_id}")

        return OAuthStartResponse(
            session_id=session_id,
            verification_url=session_data["verification_url"],
            user_code=session_data["user_code"],
            expires_in=session_data["expires_in"],
            interval=session_data["interval"],
        )
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error comunicándose con Google OAuth: {str(e)}",
        )


@router.post(
    "/oauth/poll",
    summary="Verificar autorización OAuth",
    description="""
Verifica si el usuario completó la autorización en Google.

**Polling:** Llamar cada 5 segundos (usar el `interval` de `/oauth/start`) hasta recibir
`status: "authorized"`.

**Respuestas posibles:**
- `200` con `status: "pending"` → El usuario aún no autorizó. Seguir haciendo polling.
- `200` con `status: "authorized"` → Autorización completada. Token guardado en `oauth.json`.
- `410` → Sesión expirada o denegada. Iniciar nuevo flujo con `/oauth/start`.
- `502` → Error de comunicación con Google.

**Cuando la autorización es exitosa:**
1. Se filtran campos extra de la respuesta de Google (workaround bug ytmusicapi)
2. Se escribe `oauth.json` con los campos correctos
3. Se invalida el cache del cliente YTMusic
4. Se elimina la sesión de Redis
""",
    responses={
        **FORBIDDEN_RESPONSE,
        **SESSION_NOT_FOUND_RESPONSE,
        **SESSION_EXPIRED_RESPONSE,
        **NO_CREDENTIALS_RESPONSE,
        **GOOGLE_ERROR_RESPONSE,
        200: {
            "description": "Resultado del polling",
            "content": {
                "application/json": {
                    "examples": {
                        "pending": {
                            "summary": "Esperando autorización",
                            "value": {
                                "status": "pending",
                                "message": "Waiting for user authorization",
                            },
                        },
                        "authorized": {
                            "summary": "Autorización completada",
                            "value": {
                                "status": "authorized",
                                "message": "OAuth token saved successfully",
                            },
                        },
                    }
                }
            },
        },
    },
)
async def poll_oauth_authorization(
    body: OAuthPollRequest,
    _verified: None = Depends(verify_admin_key),
):
    client = await get_redis_client()
    session_key = f"{REDIS_SESSION_PREFIX}{body.session_id}"

    session_data = await client.get(session_key)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada o expirada. Inicia un nuevo flujo OAuth.",
        )

    session = json.loads(session_data)

    creds = await get_oauth_credentials()
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="No hay credenciales OAuth configuradas.",
        )

    try:
        oauth_creds = OAuthCredentials(
            client_id=creds["client_id"],
            client_secret=creds["client_secret"],
        )
        raw_token = oauth_creds.token_from_code(session["device_code"])
    except Exception as e:
        error_msg = str(e)
        if "authorization_pending" in error_msg or "slow_down" in error_msg:
            return OAuthPollPendingResponse()
        if "expired_token" in error_msg or "access_denied" in error_msg:
            await client.delete(session_key)
            raise HTTPException(
                status_code=410,
                detail="Sesión expirada o denegada. Inicia un nuevo flujo OAuth.",
            )
        logger.error(f"Error polling OAuth: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Error comunicándose con Google OAuth: {str(e)}",
        )

    safe_token = {
        k: v
        for k, v in raw_token.items()
        if k in EXPECTED_TOKEN_FIELDS or k == "expires_at"
    }
    safe_token["expires_at"] = int(time.time()) + raw_token.get("expires_in", 3600)

    oauth_path = Path(settings.OAUTH_JSON_PATH)
    try:
        with open(oauth_path, "w", encoding="utf-8") as f:
            json.dump(safe_token, f, indent=2)
        logger.info(f"OAuth token saved to {oauth_path}")
    except Exception as e:
        logger.error(f"Error writing oauth.json: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error guardando token OAuth: {str(e)}",
        )

    await client.delete(session_key)
    reset_ytmusic_client()

    logger.info("OAuth authorization completed successfully")

    return OAuthPollAuthorizedResponse()


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Estado de autenticación",
    description="""
Verifica el estado completo de la autenticación OAuth del servicio.

**Qué verifica:**
- `has_credentials`: Si hay credenciales almacenadas (Redis o .env)
- `has_token`: Si el archivo `oauth.json` existe
- `authenticated`: Si el cliente YTMusic puede hacer requests a YouTube Music (hace una prueba real)

**Uso típico:** Llamar al cargar el panel admin para mostrar el estado actual.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Estado de autenticación",
            "content": {
                "application/json": {
                    "examples": {
                        "not_configured": {
                            "summary": "Sin credenciales",
                            "value": {
                                "authenticated": False,
                                "has_credentials": False,
                                "has_token": False,
                                "method": "oauth",
                            },
                        },
                        "credentials_only": {
                            "summary": "Credenciales sin token",
                            "value": {
                                "authenticated": False,
                                "has_credentials": True,
                                "has_token": False,
                                "method": "oauth",
                            },
                        },
                        "fully_authenticated": {
                            "summary": "Autenticado correctamente",
                            "value": {
                                "authenticated": True,
                                "has_credentials": True,
                                "has_token": True,
                                "method": "oauth",
                            },
                        },
                    }
                }
            },
        },
    },
)
async def get_auth_status(
    _verified: None = Depends(verify_admin_key),
):
    creds = await get_oauth_credentials()
    oauth_path = Path(settings.OAUTH_JSON_PATH)

    has_token = oauth_path.exists()

    authenticated = False
    if has_token and creds:
        try:
            client = get_ytmusic_client()
            test = client.get_search_suggestions("test", ignore_spelling=True)
            authenticated = bool(test)
        except Exception as e:
            logger.debug(f"Auth test failed: {e}")
            authenticated = False

    return AuthStatusResponse(
        authenticated=authenticated,
        has_credentials=bool(creds),
        has_token=has_token,
        method="oauth",
    )
