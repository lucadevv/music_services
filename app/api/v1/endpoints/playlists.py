"""Playlist endpoints - Solo lectura de playlists públicas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.playlist_service import PlaylistService

router = APIRouter()


def get_playlist_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PlaylistService:
    """Dependency to get playlist service."""
    return PlaylistService(ytmusic)


@router.get("/{playlist_id}")
async def get_playlist(
    playlist_id: str,
    limit: int = Query(100, ge=1, le=5000),
    related: bool = Query(False),
    suggestions_limit: int = Query(0, ge=0, le=50),
    service: PlaylistService = Depends(get_playlist_service)
):
    """
    Get playlist information (solo lectura de playlists públicas).
    
    Acepta tanto playlistId como browseId (se normaliza automáticamente).
    Retorna las canciones de la playlist, cada una con su videoId.
    
    **Parámetros:**
    - playlist_id: ID de la playlist (acepta browseId con prefijo VL o playlistId sin prefijo)
    - limit: Número máximo de canciones a retornar (1-5000)
    - related: Incluir canciones relacionadas
    - suggestions_limit: Límite de sugerencias
    
    **Respuesta:**
    - tracks: Lista de canciones, cada una con 'videoId' para usar en /api/v1/stream/{videoId}
    """
    try:
        return await service.get_playlist(playlist_id, limit, related, suggestions_limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
