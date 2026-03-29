"""API Keys management endpoints with PostgreSQL backend."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from app.core.database import get_db
from app.core.auth import (
    create_api_key_in_db,
    get_all_api_keys,
    update_api_key_in_db,
    delete_api_key_from_db,
)
from app.schemas.api_keys import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyListResponse,
    APIKeyVerifyResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.auth_middleware import verify_api_key_dependency

logger = logging.getLogger(__name__)

router = APIRouter(tags=["api-keys"])


@router.post(
    "/",
    response_model=APIKeyResponse,
    summary="Create new API key",
    description="Create a new API key for accessing the API. Only admins can create API keys. The generated key is returned in the response.",
)
async def create_key(
    request: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    admin_data: dict = Depends(verify_api_key_dependency),
):
    api_key_obj = await create_api_key_in_db(
        db=db,
        title=request.title,
        description=request.description,
    )
    
    return APIKeyResponse(
        key_id=api_key_obj["key_id"],
        api_key=api_key_obj["api_key"],
        title=api_key_obj["title"],
        description=api_key_obj.get("description"),
        enabled=api_key_obj["enabled"],
        created_at=api_key_obj["created_at"],
        last_used=api_key_obj.get("last_used"),
        is_admin=api_key_obj["is_admin"],
    )


@router.get(
    "/",
    response_model=APIKeyListResponse,
    summary="List all API keys",
    description="List all registered API keys. Only admins can see this list. The API keys are shown with the key masked for security.",
)
async def list_keys(
    db: AsyncSession = Depends(get_db),
    admin_data: dict = Depends(verify_api_key_dependency),
):
    keys = await get_all_api_keys(db)
    
    for key in keys:
        key["api_key"] = key["api_key"][:20] + "..."
    
    return APIKeyListResponse(
        total=len(keys),
        keys=keys,
    )


@router.get(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Get API key details",
    description="Get details of a specific API key by ID. Only admins can see the details.",
)
async def get_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    admin_data: dict = Depends(verify_api_key_dependency),
):
    result = await db.execute(
        text("SELECT key_id, api_key, title, description, enabled, is_admin, created_at, last_used FROM api_keys WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )
    
    return APIKeyResponse(
        key_id=row[0],
        api_key=row[1],
        title=row[2],
        description=row[3],
        enabled=row[4],
        created_at=row[5],
        last_used=row[6],
        is_admin=row[7],
    )


@router.patch(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="Update the title, description, or enabled status of an API key. Only admins can update API keys.",
)
async def update_key(
    key_id: str,
    request: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    admin_data: dict = Depends(verify_api_key_dependency),
):
    updated_key = await update_api_key_in_db(
        db=db,
        key_id=key_id,
        title=request.title,
        description=request.description,
        enabled=request.enabled,
    )
    
    if not updated_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )
    
    return APIKeyResponse(
        key_id=updated_key["key_id"],
        api_key=updated_key["api_key"],
        title=updated_key["title"],
        description=updated_key.get("description"),
        enabled=updated_key["enabled"],
        created_at=updated_key["created_at"],
        last_used=updated_key.get("last_used"),
        is_admin=updated_key["is_admin"],
    )


@router.delete(
    "/{key_id}",
    summary="Delete API key",
    description="Delete an API key by ID. Only admins can delete API keys. Cannot delete admin keys.",
)
async def delete_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    admin_data: dict = Depends(verify_api_key_dependency),
):
    # Check if trying to delete admin key
    result = await db.execute(
        text("SELECT is_admin FROM api_keys WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    
    row = result.fetchone()
    
    if row and row[0]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete admin API key"
        )
    
    success = await delete_api_key_from_db(db, key_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )
    
    return {"success": True, "message": "API key deleted"}


@router.post(
    "/verify",
    response_model=APIKeyVerifyResponse,
    summary="Verify API key",
    description="Verify if an API key is valid and enabled. Any user can verify their own API key.",
)
async def verify_key_endpoint(
    api_key: str,
    db: AsyncSession = Depends(get_db),
):
    key_info = await verify_api_key_from_header(
        credentials=f"Bearer {api_key}",
        db=db,
    )
    
    return APIKeyVerifyResponse(
        valid=True,
        key_id=key_info["key_id"],
        title=key_info["title"],
    )
