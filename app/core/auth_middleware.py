"""Global authentication middleware for API routes."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from typing import Optional
import logging

from app.core.api_keys import APIKeyManager

logger = logging.getLogger(__name__)

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/openapi.yaml",
}

# Paths that require admin privileges
ADMIN_PATHS = [
    "/api/v1/api-keys",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware that validates API keys for all protected routes."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication."""
        # Skip public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Missing Authorization header",
                    "message": "Include 'Authorization: Bearer <api_key>' header"
                }
            )
        
        # Verify format: "Bearer <token>"
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid Authorization header format",
                    "message": "Use 'Authorization: Bearer <api_key>' format"
                }
            )
        
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Empty Authorization token",
                    "message": "Provide a valid API key"
                }
            )
        
        # Verify API key
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT key_id, title, enabled, is_admin
                    FROM api_keys
                    WHERE api_key = :api_key
                """),
                {"api_key": token}
            )
            row = result.fetchone()
            
            if not row:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Invalid API key",
                        "message": "The provided API key is not valid"
                    }
                )
            
            key_id, title, enabled, is_admin = row
            
            if not enabled:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "API key disabled",
                        "message": "This API key has been disabled"
                    }
                )
            
            key_info = {
                "key_id": key_id,
                "title": title,
                "is_admin": is_admin,
            }
            
            await session.execute(
                text("UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE key_id = :key_id"),
                {"key_id": key_id}
            )
            await session.commit()
        
        # Store key info in request state
        request.state.api_key_info = key_info
        
        # Check admin privileges if required
        if any(request.url.path.startswith(path) for path in ADMIN_PATHS):
            if not key_info.get("is_admin"):
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Admin access required",
                        "message": "This endpoint requires admin privileges"
                    }
                )
        
        return await call_next(request)
