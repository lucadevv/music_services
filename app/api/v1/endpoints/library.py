"""Library endpoints - Simplified for public content only."""
from fastapi import APIRouter, Depends, HTTPException
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.library_service import LibraryService

router = APIRouter()


def get_library_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> LibraryService:
    """Dependency to get library service."""
    return LibraryService(ytmusic)


@router.get("/")
async def library_info():
    """Library endpoint info - most library functions require user authentication."""
    return {
        "message": "Library endpoints require user authentication. Use /api/v1/explore for public content like charts, moods, and genres.",
        "public_endpoints": {
            "explore": "/api/v1/explore",
            "charts": "/api/v1/explore/charts",
            "moods": "/api/v1/explore/moods",
            "search": "/api/v1/search"
        }
    }
