"""Watch playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.watch_service import WatchService
from app.services.stream_service import StreamService

router = APIRouter()


def get_watch_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> WatchService:
    """Dependency to get watch service."""
    return WatchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/")
async def get_watch_playlist(
    video_id: Optional[str] = Query(None, description="Video ID to start from"),
    playlist_id: Optional[str] = Query(None, description="Playlist ID"),
    limit: int = Query(25, ge=1, le=100),
    radio: bool = Query(False, description="Get radio playlist"),
    shuffle: bool = Query(False, description="Get shuffle playlist"),
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails for tracks"),
    service: WatchService = Depends(get_watch_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    Get watch playlist (next songs when playing).
    
    Returns playlist with tracks that include:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
    """
    if not video_id and not playlist_id:
        raise HTTPException(
            status_code=400, 
            detail="Se requiere 'video_id' o 'playlist_id'"
        )
    try:
        playlist_data = await service.get_watch_playlist(
            video_id=video_id,
            playlist_id=playlist_id,
            limit=limit,
            radio=radio,
            shuffle=shuffle
        )
        
        # Enrich tracks with stream URLs and thumbnails
        if include_stream_urls:
            tracks = playlist_data.get('tracks') or playlist_data.get('items') or []
            if tracks:
                enriched_tracks = await stream_service.enrich_items_with_streams(
                    tracks, 
                    include_stream_urls=True
                )
                if 'tracks' in playlist_data:
                    playlist_data['tracks'] = enriched_tracks
                elif 'items' in playlist_data:
                    playlist_data['items'] = enriched_tracks
        
        return playlist_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
