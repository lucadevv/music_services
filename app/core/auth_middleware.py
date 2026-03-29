"""Global authentication middleware for API routes."""
from fastapi import Request, HTTPException
from typing import Optional
import logging

from app.core.auth import verify_api_key_from_header

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
ADMIN_PATHS = {
    "/api/v1/api-keys",
}


class AuthMiddleware:
    """Authentication middleware that validates API keys for all protected routes."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication."""
        # Skip public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Missing Authorization header",
                    "message": "Include 'Authorization: Bearer <api_key>' header"
                }
            )
        
        # Verify format: "Bearer <token>"
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "Invalid Authorization header format",
                    "message": "Use 'Authorization: Bearer <api_key>' format"
                }
            )
        
        token = auth_header.replace("Bearer ", "")
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail={
                "error": "Empty Authorization token",
                "message": "Provide a valid API key"
                }
            )
        
        # Verify API key
        from app.core.database import get_db
        async with get_db() as db:
            key_info = await verify_api_key_from_header(
                credentials=f"Bearer {token}",
                db=db,
            )
        
        # Store key info in request state
        request.state.api_key_info = key_info
        
        # Check admin privileges if required
        if request.url.path.startswith(tuple(ADMIN_PATHS.keys())):
            if not key_info.get("is_admin"):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Admin access required",
                        "message": "This endpoint requires admin privileges"
                    }
                )
        
        return await call_next(request)
