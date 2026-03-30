"""Watch playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import time
import asyncio

from app.core.ytmusic_client import get_ytmusic
from app.core.exceptions import YTMusicServiceException
from app.schemas.watch import WatchPlaylistResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.services.watch_service import WatchService
from app.services.stream_service import StreamService

router = APIRouter()

# In-memory rate limiting para evitar llamadas duplicadas rápidas
# Key: video_id or playlist_id, Value: (timestamp, result)
_recent_requests: Dict[str, tuple] = {}
_request_lock = asyncio.Lock()
_REQUEST_TTL = 5  # Cache en memoria por 5 segundos para evitar llamadas duplicadas


async def _cleanup_old_requests():
    """Limpia entradas de cache antiguas."""
    current_time = time.time()
    async with _request_lock:
        keys_to_delete = [
            key for key, (ts, _) in _recent_requests.items()
            if current_time - ts > _REQUEST_TTL
        ]
        for key in keys_to_delete:
            del _recent_requests[key]


def get_watch_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> WatchService:
    """Dependency to get watch service."""
    return WatchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/",
    response_model=WatchPlaylistResponse,
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
        **COMMON_ERROR_RESPONSES
    }
)
async def get_watch_playlist(
    video_id: Optional[str] = Query(None, description="ID del video para iniciar", examples=["rMbATaj7Il8"]),
    playlist_id: Optional[str] = Query(None, description="ID de la playlist", examples=["PL..."]),
    limit: int = Query(25, ge=1, le=100, description="Número de canciones", examples=[25]),
    start_index: int = Query(0, ge=0, description="Índice inicial para paginación"),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Items por página"),
    radio: bool = Query(False, description="Obtener playlist de radio"),
    shuffle: bool = Query(False, description="Obtener playlist en modo shuffle"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para tracks"
    ),
    prefetch_count: int = Query(
        10, 
        ge=-1, 
        le=50,
        description="Número de URLs a obtener en paralelo (0 = none, -1 = todas)"
    ),
    service: WatchService = Depends(get_watch_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene la playlist de reproducción (siguientes canciones) con paginación estandarizada.
    
    - Requiere `video_id` o `playlist_id` (al menos uno)
    - `page`: Número de página (1 = primera página)
    - `page_size`: Items por página (default 10, máximo 50)
    - `radio=true`: Genera una playlist de radio basada en el video/playlist
    - `shuffle=true`: Mezcla las canciones aleatoriamente
    - `prefetch_count`: Cuántos tracks enriquecer con stream URLs (default: 10)
    
    Si `include_stream_urls=true` y `prefetch_count > 0`, los primeros N tracks incluyen:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    
    El resto de tracks puede obtenerse bajo demanda usando `/stream/{videoId}` o `/stream/batch`.
    """
    if not video_id and not playlist_id:
        raise HTTPException(
            status_code=400, 
            detail="Se requiere 'video_id' o 'playlist_id'"
        )

    # shuffle=True requiere playlist_id según ytmusicapi
    if shuffle and not playlist_id:
        raise HTTPException(
            status_code=400,
            detail="shuffle=True requiere playlist_id (no funciona con solo video_id)"
        )

    # Deduplicación en memoria para evitar llamadas duplicadas rápidas
    request_key = f"{video_id or playlist_id}:{start_index}:{limit}:{page}"
    current_time = time.time()

    # Limpiar cache antiguos ocasionalmente
    if len(_recent_requests) > 100:
        await _cleanup_old_requests()

    async with _request_lock:
        if request_key in _recent_requests:
            cached_time, cached_result = _recent_requests[request_key]
            if current_time - cached_time < _REQUEST_TTL:
                return cached_result

    playlist_data = await service.get_watch_playlist(
        video_id=video_id,
        playlist_id=playlist_id,
        limit=limit,
        radio=radio,
        shuffle=shuffle,
        page=page,
        page_size=page_size
    )

    # Enrich tracks with stream URLs
    if include_stream_urls and prefetch_count != 0:
        tracks = playlist_data.get('items') or []
        if tracks:
            tracks_to_enrich = tracks if prefetch_count == -1 else tracks[:prefetch_count]
            tracks_remaining = [] if prefetch_count == -1 else tracks[prefetch_count:]

            if tracks_to_enrich:
                enriched_tracks = await stream_service.enrich_items_with_streams(
                    tracks_to_enrich,
                    include_stream_urls=True
                )

                if tracks_remaining:
                    enriched_tracks.extend(tracks_remaining)

                playlist_data['items'] = enriched_tracks
                tracks_with_url = sum(1 for t in enriched_tracks if t.get('stream_url'))
                playlist_data['stream_urls_prefetched'] = tracks_with_url
                playlist_data['stream_urls_total'] = len(enriched_tracks)

    # Guardar en cache en memoria para deduplicación
    async with _request_lock:
        _recent_requests[request_key] = (current_time, playlist_data)

    return playlist_data