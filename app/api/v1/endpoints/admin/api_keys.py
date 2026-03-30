"""API Keys management endpoints with PostgreSQL backend."""
import logging
import secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from datetime import datetime

from app.core.database import get_db
from app.schemas.api_keys import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyListResponse,
    APIKeyVerifyResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


async def get_admin_key_from_db(db: AsyncSession, api_key: str) -> Optional[dict]:
    """Verify API key and return info if admin."""
    result = await db.execute(
        text("""
            SELECT key_id, title, enabled, is_admin
            FROM api_keys
            WHERE api_key = :api_key
        """),
        {"api_key": api_key}
    )
    row = result.fetchone()
    if not row:
        return None
    return {"key_id": row[0], "title": row[1], "enabled": row[2], "is_admin": row[3]}


async def get_request_api_key(request: Request) -> str:
    """Extract API key from request - tries Authorization header first, then query param."""
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    return request.query_params.get("x_api_key")


async def require_admin(db: AsyncSession, api_key: str) -> dict:
    """Dependency to require admin API key."""
    key_info = await get_admin_key_from_db(db, api_key)
    if not key_info:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not key_info["enabled"]:
        raise HTTPException(status_code=401, detail="API key is disabled")
    if not key_info["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return key_info


async def verify_master_admin_key(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key", include_in_schema=False),
) -> None:
    """Validate ADMIN_SECRET_KEY for admin-only endpoints."""
    configured_key = settings.ADMIN_SECRET_KEY
    if not configured_key:
        raise HTTPException(status_code=403, detail="ADMIN_SECRET_KEY no configurado")
    if not x_admin_key or x_admin_key != configured_key:
        raise HTTPException(status_code=403, detail="Admin key inválida")


@router.post(
    "/",
    response_model=APIKeyResponse,
    summary="Create new API key",
    description="""
    Crea una nueva API key para que usuarios puedan acceder a la API.
    
    ## Autenticación
    Requires admin key in header: `X-Admin-Key: <ADMIN_SECRET_KEY>`
    
    ## Usage
    1. Usa tu key de admin para crear una nueva key
    2. La nueva key se retorna en la respuesta (**guárdala, solo se muestra una vez**)
    3. Los usuarios usan esa key en el header `Authorization: Bearer sk_live_...`
    
    ## Ejemplo
    ```bash
    curl -X POST http://localhost:8000/api/v1/api-keys/ \\
      -H "X-Admin-Key: tu-admin-secret-key" \\
      -H "Content-Type: application/json" \\
      -d '{"title": "Mi App", "description": "App móvil"}'
    ```
    """,
    responses={
        401: {"description": "Invalid or disabled API key"},
        403: {"description": "Admin access required"},
    },
)
async def create_key(
    body: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    _verified: None = Depends(verify_master_admin_key),
):
    # Generate new API key
    new_key = f"sk_live_{secrets.token_urlsafe(24)}"
    key_id = secrets.token_urlsafe(8)
    
    await db.execute(
        text("""
            INSERT INTO api_keys (key_id, api_key, title, description, enabled, is_admin)
            VALUES (:key_id, :api_key, :title, :description, true, false)
        """),
        {
            "key_id": key_id,
            "api_key": new_key,
            "title": body.title,
            "description": body.description or "",
        }
    )
    await db.commit()
    
    return APIKeyResponse(
        key_id=key_id,
        api_key=new_key,
        title=body.title,
        description=body.description,
        enabled=True,
        created_at=datetime.now(),
        last_used=None,
        is_admin=False,
    )


@router.get(
    "/",
    response_model=APIKeyListResponse,
    summary="List all API keys",
    description="""
    Lista todas las API keys registradas en el sistema.
    
    ## Autenticación
    Requires admin key in header: `X-Admin-Key: <ADMIN_SECRET_KEY>`
    
    ## Nota de seguridad
    Las API keys se muestran truncadas (solo los primeros 20 caracteres) por seguridad.
    """,
    responses={
        401: {"description": "Invalid or disabled API key"},
        403: {"description": "Admin access required"},
    },
)
async def list_keys(
    db: AsyncSession = Depends(get_db),
    _verified: None = Depends(verify_master_admin_key),
):
    result = await db.execute(
        text("SELECT key_id, api_key, title, description, enabled, is_admin, created_at, last_used FROM api_keys")
    )
    rows = result.fetchall()
    
    keys = []
    for row in rows:
        keys.append(APIKeyResponse(
            key_id=row[0],
            api_key=row[1][:20] + "...",
            title=row[2],
            description=row[3],
            enabled=row[4],
            created_at=row[6],
            last_used=row[7],
            is_admin=row[5],
        ))
    
    return APIKeyListResponse(total=len(keys), keys=keys)


@router.get(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Get API key details",
    description="""
    Obtiene los detalles de una API key específica por su ID.
    
    ## Autenticación
    Requires admin key in header: `X-Admin-Key: <ADMIN_SECRET_KEY>`
    """,
    responses={
        401: {"description": "Invalid or disabled API key"},
        403: {"description": "Admin access required"},
        404: {"description": "API key not found"},
    },
)
async def get_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    _verified: None = Depends(verify_master_admin_key),
):
    result = await db.execute(
        text("SELECT key_id, api_key, title, description, enabled, is_admin, created_at, last_used FROM api_keys WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyResponse(
        key_id=row[0],
        api_key=row[1],
        title=row[2],
        description=row[3],
        enabled=row[4],
        created_at=row[6],
        last_used=row[7],
        is_admin=row[5],
    )


@router.patch(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="""
    Actualiza el título, descripción o estado de una API key específica.
    
    ## Autenticación
    Requires admin key in header: `X-Admin-Key: <ADMIN_SECRET_KEY>`
    
    ## Campos opcionales
    Solo envía los campos que deseas actualizar. Los campos no enviados permanecen sin cambios.
    """,
    responses={
        401: {"description": "Invalid or disabled API key"},
        403: {"description": "Admin access required"},
        404: {"description": "API key not found"},
    },
)
async def update_key(
    key_id: str,
    body: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    _verified: None = Depends(verify_master_admin_key),
):
    await db.execute(
        text("""
            UPDATE api_keys 
            SET title = COALESCE(:title, title),
                description = COALESCE(:description, description),
                enabled = COALESCE(:enabled, enabled)
            WHERE key_id = :key_id
        """),
        {
            "key_id": key_id,
            "title": body.title,
            "description": body.description,
            "enabled": body.enabled,
        }
    )
    await db.commit()
    
    result = await db.execute(
        text("SELECT key_id, api_key, title, description, enabled, is_admin, created_at, last_used FROM api_keys WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return APIKeyResponse(
        key_id=row[0],
        api_key=row[1],
        title=row[2],
        description=row[3],
        enabled=row[4],
        created_at=row[6],
        last_used=row[7],
        is_admin=row[5],
    )


@router.delete(
    "/{key_id}",
    summary="Delete API key",
    description="""
    Elimina una API key por su ID.
    
    ## Autenticación
    Requires admin key in header: `X-Admin-Key: <ADMIN_SECRET_KEY>`
    
    ## Restricciones
    No es posible eliminar las keys de administrador.
    """,
    responses={
        401: {"description": "Invalid or disabled API key"},
        403: {"description": "Admin access required"},
        404: {"description": "API key not found"},
        400: {"description": "Cannot delete admin API key"},
    },
)
async def delete_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    _verified: None = Depends(verify_master_admin_key),
):
    # Check if trying to delete admin key
    result = await db.execute(
        text("SELECT is_admin FROM api_keys WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    
    row = result.fetchone()
    
    if row and row[0]:
        raise HTTPException(status_code=400, detail="Cannot delete admin API key")
    
    await db.execute(text("DELETE FROM api_keys WHERE key_id = :key_id"), {"key_id": key_id})
    await db.commit()
    
    return {"success": True, "message": "API key deleted"}


# DEPRECATED: El endpoint de verificación ya no es necesario.
# La autenticación se maneja automáticamente con el middleware Bearer en cada request.
# Para verificar si una API key es válida, simplemente hacé un request a cualquier
# endpoint protegido - si retorna 401, la key es inválida.
