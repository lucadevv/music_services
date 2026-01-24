"""Search endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.search_service import SearchService

router = APIRouter()


def get_search_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> SearchService:
    """Dependency to get search service."""
    return SearchService(ytmusic)


@router.get("/")
async def search_music(
    q: str = Query(..., description="Search query"),
    filter: Optional[str] = Query(None, description="Filter: songs, videos, albums, artists, playlists"),
    scope: Optional[str] = Query(None, description="Search scope"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    ignore_spelling: bool = Query(False, description="Ignore spelling suggestions"),
    service: SearchService = Depends(get_search_service)
):
    """Search for music content."""
    if not q:
        raise HTTPException(status_code=400, detail="Falta el parámetro 'q'")
    try:
        results = await service.search(q, filter, scope, limit, ignore_spelling)
        return {"results": results, "query": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="Search query"),
    service: SearchService = Depends(get_search_service)
):
    """Get search suggestions."""
    try:
        suggestions = await service.get_search_suggestions(q)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/suggestions")
async def remove_search_suggestions(
    q: str = Query(..., description="Search query to remove"),
    service: SearchService = Depends(get_search_service)
):
    """Remove search suggestions."""
    try:
        result = await service.remove_search_suggestions(q)
        return {"success": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
