"""Podcast endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.exceptions import YTMusicServiceException
from app.schemas.podcast import PodcastChannelResponse, PodcastEpisodeResponse, PodcastResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.services.podcast_service import PodcastService

router = APIRouter(tags=["podcasts"])


def get_podcast_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PodcastService:
    """Dependency to get podcast service."""
    return PodcastService(ytmusic)


@router.get(
    "/channel/{channel_id}",
    response_model=PodcastChannelResponse,
    summary="Get podcast channel",
    description="Obtiene información de un canal de podcast.",
    response_description="Información del canal",
    responses={
        200: {
            "description": "Canal obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "id": "UC...",
                        "title": "Podcast Channel Name",
                        "description": "Descripción del canal de podcast",
                        "thumbnails": [
                            {
                                "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            }
                        ],
                        "subscriberCount": "100000",
                        "videoCount": 50
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_channel(
    channel_id: str = Path(..., description="ID del canal", examples={"example1": {"value": "UC..."}}),
    limit: int = Query(25, ge=1, le=100, description="Límite de resultados", examples=[25]),
    service: PodcastService = Depends(get_podcast_service)
) -> PodcastChannelResponse:
    """Obtiene información de un canal de podcast."""
    try:
        result = await service.get_channel(channel_id, limit)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/channel/{channel_id}/episodes",
    response_model=PodcastChannelResponse,
    summary="Get channel episodes",
    description="Obtiene los episodios de un canal de podcast.",
    response_description="Lista de episodios",
    responses={
        200: {
            "description": "Episodios obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "episodes": [
                            {
                                "browseId": "VL...",
                                "title": "Episode Title",
                                "description": "Episode description",
                                "lengthSeconds": "3600",
                                "publishedTime": "2 years ago",
                                "thumbnail": [
                                    {
                                        "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
                                        "width": 480,
                                        "height": 360
                                    }
                                ]
                            }
                        ],
                        "continuation": "nextPageToken..."
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_channel_episodes(
    channel_id: str = Path(..., description="ID del canal", examples={"example1": {"value": "UC..."}}),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", examples=[25]),
    params: Optional[str] = Query(None, description="Parámetros de paginación"),
    service: PodcastService = Depends(get_podcast_service)
) -> PodcastChannelResponse:
    """Obtiene los episodios de un canal de podcast."""
    try:
        result = await service.get_channel_episodes(channel_id, limit, params)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{browse_id}",
    response_model=PodcastResponse,
    summary="Get podcast",
    description="Obtiene información de un podcast específico.",
    response_description="Información del podcast",
    responses={
        200: {
            "description": "Podcast obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "browseId": "MPAD...",
                        "title": "Podcast Title",
                        "description": "Podcast description",
                        "author": "Podcast Author",
                        "thumbnail": [
                            {
                                "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            }
                        ],
                        "episodes": [
                            {
                                "browseId": "VLE...",
                                "title": "Episode Title",
                                "description": "Episode description",
                                "lengthSeconds": "3600",
                                "publishedTime": "2 years ago"
                            }
                        ],
                        "albums": []
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_podcast(
    browse_id: str = Path(..., description="Browse ID del podcast", examples={"example1": {"value": "MPAD..."}}),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", examples=[25]),
    service: PodcastService = Depends(get_podcast_service)
) -> PodcastResponse:
    """Obtiene información de un podcast específico."""
    try:
        result = await service.get_podcast(browse_id, limit)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/episode/{browse_id}",
    response_model=PodcastEpisodeResponse,
    summary="Get podcast episode",
    description="Obtiene información de un episodio específico de podcast.",
    response_description="Información del episodio",
    responses={
        200: {
            "description": "Episodio obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "browseId": "VLE...",
                        "title": "Episode Title",
                        "description": "Episode description",
                        "author": "Podcast Author",
                        "lengthSeconds": "3600",
                        "publishedTime": "2 years ago",
                        "thumbnail": [
                            {
                                "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
                                "width": 480,
                                "height": 360
                            }
                        ],
                        "views": "100000",
                        "likes": "5000",
                        "isAvailable": True,
                        "isExplicit": False
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_episode(
    browse_id: str = Path(..., description="Browse ID del episodio", examples={"example1": {"value": "MPAD..."}}),
    service: PodcastService = Depends(get_podcast_service)
) -> PodcastEpisodeResponse:
    """Obtiene información de un episodio específico de podcast."""
    try:
        result = await service.get_episode(browse_id)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/episodes/{browse_id}/playlist",
    response_model=PodcastResponse,
    summary="Get episodes playlist",
    description="Obtiene la playlist de episodios de un podcast.",
    response_description="Playlist de episodios",
    responses={
        200: {
            "description": "Playlist obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Podcast Playlist",
                        "description": "Episodios del podcast",
                        "trackCount": 10,
                        "tracks": [
                            {
                                "videoId": "abc123",
                                "title": "Episode Title",
                                "artists": [{"name": "Podcast Author"}],
                                "album": {"name": "Podcast Name"},
                                "duration": "3600",
                                "isExplicit": False,
                                "stream_url": "https://...",
                                "thumbnail": [
                                    {
                                        "url": "https://i.ytimg.com/vi/.../hqdefault.jpg",
                                        "width": 480,
                                        "height": 360
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_episodes_playlist(
    browse_id: str = Path(..., description="Browse ID del podcast", examples={"example1": {"value": "MPAD..."}}),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", examples=[25]),
    service: PodcastService = Depends(get_podcast_service)
) -> PodcastResponse:
    """Obtiene la playlist de episodios de un podcast."""
    try:
        result = await service.get_episodes_playlist(browse_id, limit)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
