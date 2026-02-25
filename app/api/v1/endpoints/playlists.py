"""Playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.playlist_service import PlaylistService
from app.services.stream_service import StreamService

router = APIRouter(tags=["playlists"])


def get_playlist_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> PlaylistService:
    """Dependency to get playlist service."""
    return PlaylistService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/{playlist_id}",
    summary="Get playlist",
    description="Obtiene información completa de una playlist pública incluyendo todas sus canciones.",
    response_description="Información de la playlist con tracks",
    responses={
        200: {
            "description": "Playlist obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Playlist Title",
                        "trackCount": 50,
                        "tracks": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Track Title",
                                "artists": [{"name": "Artist"}],
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ]
                    }
                }
            }
        },
        500: {"description": "Error interno"}
    }
)
async def get_playlist(
    playlist_id: str = Path(..., description="ID de la playlist (acepta browseId con prefijo VL)", examples={"example1": {"value": "PL..."}}),
    limit: int = Query(100, ge=1, le=5000, description="Número máximo de canciones", examples=[100]),
    related: bool = Query(False, description="Incluir canciones relacionadas"),
    suggestions_limit: int = Query(0, ge=0, le=50, description="Límite de sugerencias"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para tracks"
    ),
    service: PlaylistService = Depends(get_playlist_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene información completa de una playlist pública.
    
    - Acepta `playlistId` o `browseId` (con prefijo VL, se normaliza automáticamente)
    - Retorna todas las canciones de la playlist
    
    Si `include_stream_urls=true`, cada track incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
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
