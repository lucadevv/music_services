"""Authentication system with PostgreSQL backend."""
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.config import get_settings
from app.core.cache_redis import get_cached_value, set_cached_value

settings = get_settings()
security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify API key with Redis caching to avoid database bottlenecks.
    """
    token = credentials.credentials
    
    # 1. Check Redis cache first
    cache_key = f"auth:api_key:{token}"
    cached_info = await get_cached_value(cache_key)
    if cached_info:
        return cached_info

    # 2. Query database if not in cache
    query = text("""
        SELECT key_id, title, description, enabled, is_admin, created_at
        FROM api_keys
        WHERE api_key = :api_key
    """)
    
    result = await db.execute(query, {"api_key": token})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    key_id, title, description, enabled, is_admin, created_at = row
    
    if not enabled:
        raise HTTPException(
            status_code=401,
            detail="API key is disabled"
        )
    
    key_info = {
        "key_id": key_id,
        "title": title,
        "description": description,
        "is_admin": is_admin,
        "created_at": str(created_at) if created_at else None,
    }
    
    # 3. Store in Redis for 5 minutes (300s)
    await set_cached_value(cache_key, key_info, ttl=300)
    
    # Note: Removed UPDATE last_used for performance under high load.
    # Consider doing this asynchronously or only once per hour.
    
    return key_info


async def verify_admin_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify admin API key. Must have is_admin=True.
    
    Returns dict with key info if valid admin.
    Raises HTTPException 401/403 if invalid or not admin.
    """
    key_info = await verify_api_key(credentials, db)
    
    if not key_info["is_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return key_info


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"sk_live_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()
