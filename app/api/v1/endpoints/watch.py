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
    video_id: Optional[str] = Query(None, description="ID del video para iniciar", examples=["rMbATaj7Il8"]),
    playlist_id: Optional[str] = Query(None, description="ID de la playlist", examples=["PL..."]),
    limit: int = Query(25, ge=1, le=100, description="Número de canciones", examples=[25]),
    start_index: int = Query(0, ge=0, description="Índice inicial para paginación"),
    radio: bool = Query(False, description="Obtener playlist de radio"),
    shuffle: bool = Query(False, description="Obtener playlist en modo shuffle"),
    include_stream_urls: bool = Query(
        False, 
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
    Obtiene la playlist de reproducción (siguientes canciones).
    
    - Requiere `video_id` o `playlist_id` (al menos uno)
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
    
    from app.core.cache_redis import get_cached_value, set_cached_value
    
    cache_key = f"music:endpoint:watch:{video_id or ''}:{playlist_id or ''}:{limit}:{start_index}:{radio}:{shuffle}:{include_stream_urls}:{prefetch_count}"
    cached = await get_cached_value(cache_key)
    if cached:
        return cached
    
    try:
        playlist_data = await service.get_watch_playlist(
            video_id=video_id,
            playlist_id=playlist_id,
            limit=limit,
            radio=radio,
            shuffle=shuffle
        )
        
        # Enrich tracks with stream URLs
        if include_stream_urls and prefetch_count != 0:
            tracks = playlist_data.get('tracks') or playlist_data.get('items') or []
            if tracks:
                if start_index > 0 and start_index < len(tracks):
                    tracks = tracks[start_index:]
                
                if limit > 0 and limit < len(tracks):
                    tracks = tracks[:limit]
                
                if 'tracks' in playlist_data:
                    playlist_data['tracks'] = tracks
                elif 'items' in playlist_data:
                    playlist_data['items'] = tracks
                
                tracks_to_enrich = tracks if prefetch_count == -1 else tracks[:prefetch_count]
                tracks_remaining = [] if prefetch_count == -1 else tracks[prefetch_count:]
                
                if tracks_to_enrich:
                    enriched_tracks = await stream_service.enrich_items_with_streams(
                        tracks_to_enrich, 
                        include_stream_urls=True
                    )
                    
                    if tracks_remaining:
                        enriched_tracks.extend(tracks_remaining)
                    
                    if 'tracks' in playlist_data:
                        playlist_data['tracks'] = enriched_tracks
                    elif 'items' in playlist_data:
                        playlist_data['items'] = enriched_tracks
                        
                    tracks_with_url = sum(1 for t in enriched_tracks if t.get('stream_url'))
                    playlist_data['stream_urls_prefetched'] = tracks_with_url
                    playlist_data['stream_urls_total'] = len(enriched_tracks)
        else:
            tracks = playlist_data.get('tracks') or playlist_data.get('items') or []
            if tracks:
                if start_index > 0 and start_index < len(tracks):
                    tracks = tracks[start_index:]
                if limit > 0 and limit < len(tracks):
                    tracks = tracks[:limit]
                if 'tracks' in playlist_data:
                    playlist_data['tracks'] = tracks
                elif 'items' in playlist_data:
                    playlist_data['items'] = tracks
        
        try:
            await set_cached_value(cache_key, playlist_data, ttl=300)
        except Exception:
            pass
        
        return playlist_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
