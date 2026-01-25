"""Search endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.search_service import SearchService
from app.services.stream_service import StreamService

router = APIRouter()


def get_search_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> SearchService:
    """Dependency to get search service."""
    return SearchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/")
async def search_music(
    q: str = Query(..., description="Search query"),
    filter: Optional[str] = Query(None, description="Filter: songs, videos, albums, artists, playlists"),
    scope: Optional[str] = Query(None, description="Search scope"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    ignore_spelling: bool = Query(False, description="Ignore spelling suggestions"),
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails for songs/videos"),
    service: SearchService = Depends(get_search_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    Search for music content.
    
    When filter is 'songs' or 'videos', results include:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
    """
    if not q:
        raise HTTPException(status_code=400, detail="Falta el parámetro 'q'")
    try:
        results = await service.search(q, filter, scope, limit, ignore_spelling)
        
        # Enrich songs/videos with stream URLs and thumbnails
        if include_stream_urls and filter in ['songs', 'videos', None]:
            # Filter items that have videoId
            items_to_enrich = [r for r in results if r.get('videoId')]
            if items_to_enrich:
                enriched_items = await stream_service.enrich_items_with_streams(
                    items_to_enrich, 
                    include_stream_urls=True
                )
                # Map enriched items back to results - preserve ALL original fields
                enriched_map = {item.get('videoId'): item for item in enriched_items if item.get('videoId')}
                for i, result in enumerate(results):
                    video_id = result.get('videoId')
                    if video_id and video_id in enriched_map:
                        # enriched_map contains ALL original fields + stream_url + thumbnail
                        # Replace the entire result with the enriched version (which has all fields)
                        results[i] = enriched_map[video_id]
        
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
