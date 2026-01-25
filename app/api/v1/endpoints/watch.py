"""Watch playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.watch_service import WatchService
from app.services.stream_service import StreamService

router = APIRouter(tags=["watch"])


def get_watch_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> WatchService:
    """Dependency to get watch service."""
    return WatchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/",
    summary="Get watch playlist",
    description="Obtiene la playlist de reproducción (siguientes canciones) basada en un video o playlist. Soporta radio y shuffle.",
    response_description="Playlist de reproducción con tracks",
    responses={
        200: {
            "description": "Playlist obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "tracks": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Next Song",
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Se requiere video_id o playlist_id"},
        500: {"description": "Error interno"}
    }
)
async def get_watch_playlist(
    video_id: Optional[str] = Query(None, description="ID del video para iniciar", example="rMbATaj7Il8"),
    playlist_id: Optional[str] = Query(None, description="ID de la playlist", example="PL..."),
    limit: int = Query(25, ge=1, le=100, description="Número de canciones", example=25),
    radio: bool = Query(False, description="Obtener playlist de radio"),
    shuffle: bool = Query(False, description="Obtener playlist en modo shuffle"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para tracks"
    ),
    service: WatchService = Depends(get_watch_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene la playlist de reproducción (siguientes canciones).
    
    - Requiere `video_id` o `playlist_id` (al menos uno)
    - `radio=true`: Genera una playlist de radio basada en el video/playlist
    - `shuffle=true`: Mezcla las canciones aleatoriamente
    
    Si `include_stream_urls=true`, cada track incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
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
