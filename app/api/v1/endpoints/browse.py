"""Browse endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.browse_service import BrowseService

router = APIRouter()


def get_browse_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> BrowseService:
    """Dependency to get browse service."""
    return BrowseService(ytmusic)


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
    service: BrowseService = Depends(get_browse_service)
):
    """Get album information."""
    try:
        return await service.get_album(album_id)
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
    service: BrowseService = Depends(get_browse_service)
):
    """Get related songs."""
    try:
        return await service.get_song_related(video_id)
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


