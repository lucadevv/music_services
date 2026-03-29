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

settings = get_settings()
security = HTTPBearer()


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verify API key from Authorization header.
    
    Returns dict with key info if valid.
    Raises HTTPException 401 if invalid.
    """
    token = credentials.credentials
    
    # Query database for API key
    query = text("""
        SELECT key_id, api_key, title, description, enabled, is_admin, created_at, last_used
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
    
    key_id, api_key, title, description, enabled, is_admin, created_at, last_used = row
    
    if not enabled:
        raise HTTPException(
            status_code=401,
            detail="API key is disabled"
        )
    
    # Update last_used timestamp
    await db.execute(
        text("UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE key_id = :key_id"),
        {"key_id": key_id}
    )
    await db.commit()
    
    return {
        "key_id": key_id,
        "title": title,
        "description": description,
        "is_admin": is_admin,
        "created_at": created_at,
    }


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
