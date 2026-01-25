"""Browse endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.browse_service import BrowseService
from app.services.stream_service import StreamService

router = APIRouter()


def get_browse_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> BrowseService:
    """Dependency to get browse service."""
    return BrowseService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/home")
async def get_home(service: BrowseService = Depends(get_browse_service)):
    """Get home page content."""
    try:
        return await service.get_home()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/artist/{channel_id}")
async def get_artist(
    channel_id: str,
    service: BrowseService = Depends(get_browse_service)
):
    """Get artist information."""
    try:
        return await service.get_artist(channel_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/artist/{channel_id}/albums")
async def get_artist_albums(
    channel_id: str,
    params: Optional[str] = Query(None),
    service: BrowseService = Depends(get_browse_service)
):
    """Get artist albums."""
    try:
        return await service.get_artist_albums(channel_id, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/album/{album_id}")
async def get_album(
    album_id: str,
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails for tracks"),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    Get album information.
    
    Returns album with tracks that include:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
    """
    try:
        album_data = await service.get_album(album_id)
        
        # Enrich tracks with stream URLs and thumbnails
        if include_stream_urls:
            # ytmusicapi returns tracks in different structures, check common ones
            tracks = album_data.get('tracks') or album_data.get('songs') or []
            if tracks:
                enriched_tracks = await stream_service.enrich_items_with_streams(
                    tracks, 
                    include_stream_urls=True
                )
                if 'tracks' in album_data:
                    album_data['tracks'] = enriched_tracks
                elif 'songs' in album_data:
                    album_data['songs'] = enriched_tracks
        
        return album_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/album/{album_id}/browse-id")
async def get_album_browse_id(
    album_id: str,
    service: BrowseService = Depends(get_browse_service)
):
    """Get album browse ID."""
    try:
        browse_id = await service.get_album_browse_id(album_id)
        return {"browse_id": browse_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/song/{video_id}")
async def get_song(
    video_id: str,
    signature_timestamp: Optional[int] = Query(None),
    service: BrowseService = Depends(get_browse_service)
):
    """Get song metadata."""
    try:
        return await service.get_song(video_id, signature_timestamp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/song/{video_id}/related")
async def get_song_related(
    video_id: str,
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails"),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    Get related songs.
    
    Returns list of related songs with:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
    """
    try:
        related_songs = await service.get_song_related(video_id)
        
        # Enrich with stream URLs and thumbnails
        if include_stream_urls and related_songs:
            related_songs = await stream_service.enrich_items_with_streams(
                related_songs, 
                include_stream_urls=True
            )
        
        return related_songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lyrics/{browse_id}")
async def get_lyrics(
    browse_id: str,
    service: BrowseService = Depends(get_browse_service)
):
    """Get song lyrics."""
    try:
        return await service.get_lyrics(browse_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


