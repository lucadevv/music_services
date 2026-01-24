"""Middleware for rate limiting and performance."""
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
import time
from typing import Callable

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    storage_uri="memory://"  # In-memory storage (can be changed to Redis)
)

# Custom rate limit handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    response = HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {settings.RATE_LIMIT_PER_MINUTE} requests per minute.",
            "retry_after": int(exc.retry_after) if exc.retry_after else 60
        }
    )
    return response

# Register handler
limiter._rate_limit_exceeded_handler = rate_limit_handler
