"""Podcast endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.podcast_service import PodcastService

router = APIRouter()


def get_podcast_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PodcastService:
    """Dependency to get podcast service."""
    return PodcastService(ytmusic)


@router.get("/channel/{channel_id}")
async def get_channel(
    channel_id: str,
    limit: int = Query(25, ge=1, le=100),
    service: PodcastService = Depends(get_podcast_service)
):
    """Get channel information."""
    try:
        return await service.get_channel(channel_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channel/{channel_id}/episodes")
async def get_channel_episodes(
    channel_id: str,
    limit: int = Query(25, ge=1, le=100),
    params: Optional[str] = Query(None),
    service: PodcastService = Depends(get_podcast_service)
):
    """Get channel episodes."""
    try:
        return await service.get_channel_episodes(channel_id, limit, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{browse_id}")
async def get_podcast(
    browse_id: str,
    limit: int = Query(25, ge=1, le=100),
    service: PodcastService = Depends(get_podcast_service)
):
    """Get podcast information."""
    try:
        return await service.get_podcast(browse_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episode/{browse_id}")
async def get_episode(
    browse_id: str,
    service: PodcastService = Depends(get_podcast_service)
):
    """Get episode information."""
    try:
        return await service.get_episode(browse_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodes/{browse_id}/playlist")
async def get_episodes_playlist(
    browse_id: str,
    limit: int = Query(25, ge=1, le=100),
    service: PodcastService = Depends(get_podcast_service)
):
    """Get episodes playlist."""
    try:
        return await service.get_episodes_playlist(browse_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
