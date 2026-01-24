"""API v1 router."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    browse,
    explore,
    search,
    library,
    playlists,
    watch,
    podcasts,
    uploads,
    stream,
    stats
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(browse.router, prefix="/browse", tags=["browse"])
api_router.include_router(explore.router, prefix="/explore", tags=["explore"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(library.router, prefix="/library", tags=["library"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(watch.router, prefix="/watch", tags=["watch"])
api_router.include_router(podcasts.router, prefix="/podcasts", tags=["podcasts"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])