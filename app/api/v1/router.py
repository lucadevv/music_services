"""API v1 router."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    api_keys,
    auth,
    browse,
    explore,
    search,
    playlists,
    watch,
    podcasts,
    stream,
    stats
)

from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(browse.router, prefix="/browse", tags=["browse"])
api_router.include_router(explore.router, prefix="/explore", tags=["explore"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(watch.router, prefix="/watch", tags=["watch"])
api_router.include_router(podcasts.router, prefix="/podcasts", tags=["podcasts"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
