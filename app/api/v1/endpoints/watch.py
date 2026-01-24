"""Watch playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.watch_service import WatchService

router = APIRouter()


def get_watch_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> WatchService:
    """Dependency to get watch service."""
    return WatchService(ytmusic)


@router.get("/")
async def get_watch_playlist(
    video_id: Optional[str] = Query(None, description="Video ID to start from"),
    playlist_id: Optional[str] = Query(None, description="Playlist ID"),
    limit: int = Query(25, ge=1, le=100),
    radio: bool = Query(False, description="Get radio playlist"),
    shuffle: bool = Query(False, description="Get shuffle playlist"),
    service: WatchService = Depends(get_watch_service)
):
    """Get watch playlist (next songs when playing)."""
    if not video_id and not playlist_id:
        raise HTTPException(
            status_code=400, 
            detail="Se requiere 'video_id' o 'playlist_id'"
        )
    try:
        return await service.get_watch_playlist(
            video_id=video_id,
            playlist_id=playlist_id,
            limit=limit,
            radio=radio,
            shuffle=shuffle
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
