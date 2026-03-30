"""API v1 router."""
from fastapi import APIRouter, Depends
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.music import router as music_router

from app.core.config import get_settings
from app.core.auth_docs import require_music_bearer_header

settings = get_settings()

api_router = APIRouter()

# --- ADMIN ROUTER (/api/v1/admin) ---
api_router.include_router(
    admin_router, 
    prefix="/admin", 
    tags=["Admin"]
)

# --- MUSIC ROUTER (/api/v1/music) ---
api_router.include_router(
    music_router, 
    prefix="/music", 
    tags=["Music"], 
    dependencies=[Depends(require_music_bearer_header)]
)
