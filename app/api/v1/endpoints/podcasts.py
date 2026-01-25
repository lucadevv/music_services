"""Podcast endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.podcast_service import PodcastService

router = APIRouter(tags=["podcasts"])


def get_podcast_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PodcastService:
    """Dependency to get podcast service."""
    return PodcastService(ytmusic)


@router.get(
    "/channel/{channel_id}",
    summary="Get podcast channel",
    description="Obtiene información de un canal de podcast.",
    response_description="Información del canal",
    responses={200: {"description": "Canal obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_channel(
    channel_id: str = Query(..., description="ID del canal", example="UC..."),
    limit: int = Query(25, ge=1, le=100, description="Límite de resultados", example=25),
    service: PodcastService = Depends(get_podcast_service)
) -> Dict[str, Any]:
    """Obtiene información de un canal de podcast."""
    try:
        return await service.get_channel(channel_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/channel/{channel_id}/episodes",
    summary="Get channel episodes",
    description="Obtiene los episodios de un canal de podcast.",
    response_description="Lista de episodios",
    responses={200: {"description": "Episodios obtenidos exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_channel_episodes(
    channel_id: str = Query(..., description="ID del canal", example="UC..."),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", example=25),
    params: Optional[str] = Query(None, description="Parámetros de paginación"),
    service: PodcastService = Depends(get_podcast_service)
) -> Dict[str, Any]:
    """Obtiene los episodios de un canal de podcast."""
    try:
        return await service.get_channel_episodes(channel_id, limit, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{browse_id}",
    summary="Get podcast",
    description="Obtiene información de un podcast específico.",
    response_description="Información del podcast",
    responses={200: {"description": "Podcast obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_podcast(
    browse_id: str = Query(..., description="Browse ID del podcast", example="MPAD..."),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", example=25),
    service: PodcastService = Depends(get_podcast_service)
) -> Dict[str, Any]:
    """Obtiene información de un podcast específico."""
    try:
        return await service.get_podcast(browse_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/episode/{browse_id}",
    summary="Get podcast episode",
    description="Obtiene información de un episodio específico de podcast.",
    response_description="Información del episodio",
    responses={200: {"description": "Episodio obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_episode(
    browse_id: str = Query(..., description="Browse ID del episodio", example="MPAD..."),
    service: PodcastService = Depends(get_podcast_service)
) -> Dict[str, Any]:
    """Obtiene información de un episodio específico de podcast."""
    try:
        return await service.get_episode(browse_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/episodes/{browse_id}/playlist",
    summary="Get episodes playlist",
    description="Obtiene la playlist de episodios de un podcast.",
    response_description="Playlist de episodios",
    responses={200: {"description": "Playlist obtenida exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_episodes_playlist(
    browse_id: str = Query(..., description="Browse ID del podcast", example="MPAD..."),
    limit: int = Query(25, ge=1, le=100, description="Límite de episodios", example=25),
    service: PodcastService = Depends(get_podcast_service)
) -> Dict[str, Any]:
    """Obtiene la playlist de episodios de un podcast."""
    try:
        return await service.get_episodes_playlist(browse_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
