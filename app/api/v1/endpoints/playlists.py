"""Playlist endpoints - Solo lectura de playlists públicas."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.playlist_service import PlaylistService
from app.services.stream_service import StreamService

router = APIRouter()


def get_playlist_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PlaylistService:
    """Dependency to get playlist service."""
    return PlaylistService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/{playlist_id}")
async def get_playlist(
    playlist_id: str,
    limit: int = Query(100, ge=1, le=5000),
    related: bool = Query(False),
    suggestions_limit: int = Query(0, ge=0, le=50),
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails for tracks"),
    service: PlaylistService = Depends(get_playlist_service),
    stream_service: StreamService = Depends(get_stream_service)
):
    """
    Get playlist information (solo lectura de playlists públicas).
    
    Acepta tanto playlistId como browseId (se normaliza automáticamente).
    Retorna las canciones de la playlist con:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
    
    **Parámetros:**
    - playlist_id: ID de la playlist (acepta browseId con prefijo VL o playlistId sin prefijo)
    - limit: Número máximo de canciones a retornar (1-5000)
    - related: Incluir canciones relacionadas
    - suggestions_limit: Límite de sugerencias
    - include_stream_urls: Incluir URLs de stream y mejores thumbnails (default: true)
    
    **Respuesta:**
    - tracks: Lista de canciones con 'stream_url' y 'thumbnail' (mejor calidad)
    """
    try:
        playlist_data = await service.get_playlist(playlist_id, limit, related, suggestions_limit)
        
        # Enrich tracks with stream URLs and thumbnails
        if include_stream_urls and playlist_data.get('tracks'):
            tracks = playlist_data['tracks']
            enriched_tracks = await stream_service.enrich_items_with_streams(
                tracks, 
                include_stream_urls=True
            )
            playlist_data['tracks'] = enriched_tracks
        
        return playlist_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
