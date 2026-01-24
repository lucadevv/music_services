"""Stats and monitoring endpoints."""
from fastapi import APIRouter, Depends
from app.core.cache import get_cache_stats
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/stats")
async def get_stats():
    """Get service statistics."""
    cache_stats = get_cache_stats()
    
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
        },
        "caching": cache_stats,
        "performance": {
            "compression": settings.ENABLE_COMPRESSION,
            "http_timeout": settings.HTTP_TIMEOUT,
            "max_workers": settings.MAX_WORKERS
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }
