"""Admin endpoints router."""
from fastapi import APIRouter
from app.api.v1.endpoints.admin import (
    api_keys,
    auth,
    stats,
    cache
)

router = APIRouter()

# Include admin sub-routers
router.include_router(api_keys.router, prefix="/api-keys", tags=["Admin: API Keys"])
router.include_router(auth.router, prefix="/auth", tags=["Admin: Auth"])
router.include_router(stats.router, prefix="/stats", tags=["Admin: Stats"])
router.include_router(cache.router, prefix="/cache", tags=["Admin: Cache"])
