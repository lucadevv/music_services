"""Browser authentication endpoints for admin panel."""
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
import httpx

from app.core.config import get_settings
from app.core.browser_client import (
    get_browser_manager,
    get_auth_status,
    reset_client_cache,
    get_ytmusic,
)
from app.schemas.auth import (
    BrowserAddResponse,
    BrowserListResponse,
    BrowserAccountInfo,
    BrowserTestResponse,
    AuthStatusResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

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


async def verify_admin_key(
    x_admin_key: Optional[str] = Header(
        None,
        alias="X-Admin-Key",
        description="Clave secreta de administrador (configurada en .env como ADMIN_SECRET_KEY)",
        examples=["mi-clave-super-secreta"],
    ),
) -> None:
    """Verify the admin key from request header."""
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


@router.post(
    "/browser/from-url",
    response_model=BrowserAddResponse,
    summary="Agregar cuenta desde URL",
    description="""
Agrega una cuenta de navegador descargando los headers desde una URL.

La URL debe devolver los headers de autenticación de YouTube Music en formato JSON.

**Cómo obtener los headers:**
1. Abrí YouTube Music en Chrome/Firefox
2. Abrí DevTools (F12) > Network
3. Hacé cualquier request a music.youtube.com
4. Copiá los headers del request ( Authorization, X-YouTube-Music-DevKey, etc.)
5. Subí un archivo JSON con esos headers a cualquier hosting
6. Pasá la URL aquí

**También podés usar el endpoint `/browser/from-headers` para pasar los headers directamente.**
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Cuenta agregada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "account_name": "account_1",
                        "message": "Cuenta agregada exitosamente"
                    }
                }
            },
        },
        400: {
            "description": "URL inválida o no accessible",
            "content": {
                "application/json": {
                    "example": {"detail": "No se pudo descargar headers de la URL"}
                }
            },
        },
    },
)
async def add_browser_account_from_url(
    url: str,
    name: Optional[str] = None,
    _verified: None = Depends(verify_admin_key),
):
    """Download and add browser account from a URL."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            headers = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo descargar headers de la URL: {str(e)}",
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="La URL no devuelve JSON válido",
        )
    
    if not isinstance(headers, dict):
        raise HTTPException(
            status_code=400,
            detail="El JSON debe ser un objeto con los headers",
        )
    
    account_name = name or f"account_{int(time.time())}"
    
    try:
        saved_name = get_browser_manager().add_account(account_name, headers)
        reset_client_cache()
        
        return BrowserAddResponse(
            success=True,
            account_name=saved_name,
            message="Cuenta agregada exitosamente",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al guardar cuenta: {str(e)}",
        )


@router.post(
    "/browser/from-headers",
    response_model=BrowserAddResponse,
    summary="Agregar cuenta desde headers",
    description="""
Agrega una cuenta de navegador pasando los headers directamente.

**Cómo obtener los headers:**
1. Abrí YouTube Music en Chrome/Firefox
2. Abrí DevTools (F12) > Network
3. Hacé cualquier request a music.youtube.com
4. Copiá todos los headers del request
5. Pegalos aquí en formato JSON

Los headers típicos incluyen:
- Authorization
- X-YouTube-Music-DevKey
- X-YouTube-Client-Name
- X-YouTube-Client-Version
- Cookie (si está disponible)
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Cuenta agregada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "account_name": "cuenta_1",
                        "message": "Cuenta agregada exitosamente"
                    }
                }
            },
        },
        400: {
            "description": "Headers inválidos",
            "content": {
                "application/json": {
                    "example": {"detail": "Headers inválidos o incompletos"}
                }
            },
        },
    },
)
async def add_browser_account_from_headers(
    headers: dict,
    name: Optional[str] = None,
    _verified: None = Depends(verify_admin_key),
):
    """Add browser account from raw headers."""
    if not headers or not isinstance(headers, dict):
        raise HTTPException(
            status_code=400,
            detail="Headers inválidos o incompletos",
        )
    
    account_name = name or f"cuenta_{int(time.time())}"
    
    try:
        saved_name = get_browser_manager().add_account(account_name, headers)
        reset_client_cache()
        
        return BrowserAddResponse(
            success=True,
            account_name=saved_name,
            message="Cuenta agregada exitosamente",
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al guardar cuenta: {str(e)}",
        )


@router.get(
    "/browser",
    response_model=BrowserListResponse,
    summary="Listar cuentas",
    description="""
Lista todas las cuentas de navegador disponibles y su estado.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Lista de cuentas",
            "content": {
                "application/json": {
                    "example": {
                        "total": 2,
                        "available": 1,
                        "accounts": [
                            {
                                "name": "cuenta_1",
                                "available": True,
                                "error_count": 0,
                                "rate_limited_until": None,
                                "last_used": 1234567890.0
                            },
                            {
                                "name": "cuenta_2",
                                "available": False,
                                "error_count": 5,
                                "rate_limited_until": 1234567890.0,
                                "last_used": 1234567880.0
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def list_browser_accounts(
    _verified: None = Depends(verify_admin_key),
):
    """List all browser accounts."""
    manager = get_browser_manager()
    accounts = manager.list_accounts()
    available = manager.get_available_accounts()
    
    return BrowserListResponse(
        total=len(accounts),
        available=len(available),
        accounts=[BrowserAccountInfo(**acc) for acc in accounts],
    )


@router.delete(
    "/browser/{account_name}",
    summary="Eliminar cuenta",
    description="""
Elimina una cuenta de navegador por nombre.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Cuenta eliminada",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Cuenta eliminada"
                    }
                }
            },
        },
        404: {
            "description": "Cuenta no encontrada",
            "content": {
                "application/json": {
                    "example": {"detail": "Cuenta no encontrada"}
                }
            },
        },
    },
)
async def delete_browser_account(
    account_name: str,
    _verified: None = Depends(verify_admin_key),
):
    """Delete a browser account."""
    success = get_browser_manager().remove_account(account_name)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Cuenta no encontrada",
        )
    
    reset_client_cache()
    
    return {"success": True, "message": "Cuenta eliminada"}


@router.post(
    "/browser/test",
    response_model=BrowserTestResponse,
    summary="Probar autenticación",
    description="""
Prueba la autenticación con YouTube Music.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Resultado del test",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Autenticación exitosa",
                        "account_used": "cuenta_1"
                    }
                }
            },
        },
        503: {
            "description": "Sin cuentas disponibles",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "No hay cuentas disponibles"
                    }
                }
            },
        },
    },
)
async def test_authentication(
    _verified: None = Depends(verify_admin_key),
):
    """Test authentication with YouTube Music."""
    try:
        client = get_ytmusic()
        result = client.get_search_suggestions("test", ignore_spelling=True)
        
        manager = get_browser_manager()
        available = manager.get_available_accounts()
        account_used = available[0].name if available else "unknown"
        
        return BrowserTestResponse(
            success=True,
            message="Autenticación exitosa",
            account_used=account_used,
        )
    except Exception as e:
        return BrowserTestResponse(
            success=False,
            message=f"Error: {str(e)}",
            account_used=None,
        )


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Estado de autenticación",
    description="""
Verifica el estado de la autenticación del servicio.
""",
    responses={
        **FORBIDDEN_RESPONSE,
        200: {
            "description": "Estado de autenticación",
            "content": {
                "application/json": {
                    "example": {
                        "authenticated": True,
                        "method": "browser",
                        "total_accounts": 2,
                        "available_accounts": 1,
                        "accounts": []
                    }
                }
            },
        },
    },
)
async def get_auth_status_endpoint(
    _verified: None = Depends(verify_admin_key),
):
    """Get authentication status."""
    status = get_auth_status()
    return AuthStatusResponse(**status)
