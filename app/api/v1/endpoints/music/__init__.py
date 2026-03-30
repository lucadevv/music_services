"""Music endpoints router."""
from fastapi import APIRouter
from app.api.v1.endpoints.music import (
    browse,
    explore,
    search,
    playlists,
    watch,
    stream,
    ytdlp
)

router = APIRouter()

# Include music sub-routers
router.include_router(search.router, prefix="/search", tags=["Music: Search"])
router.include_router(browse.router, prefix="/browse", tags=["Music: Browse"])
router.include_router(explore.router, prefix="/explore", tags=["Music: Explore"])
router.include_router(playlists.router, prefix="/playlists", tags=["Music: Playlists"])
router.include_router(watch.router, prefix="/watch", tags=["Music: Watch"])
router.include_router(stream.router, prefix="/stream", tags=["Music: Stream"])
router.include_router(ytdlp.router, prefix="/ytdlp", tags=["Music: yt-dlp"])
