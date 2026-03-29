"""API v1 router."""
from fastapi import APIRouter, Depends
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
from app.core.auth_docs import require_music_bearer_header

settings = get_settings()

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(browse.router, prefix="/browse", tags=["browse"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(explore.router, prefix="/explore", tags=["explore"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(search.router, prefix="/search", tags=["search"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(watch.router, prefix="/watch", tags=["watch"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(podcasts.router, prefix="/podcasts", tags=["podcasts"], dependencies=[Depends(require_music_bearer_header)])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
