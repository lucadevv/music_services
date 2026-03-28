"""Playlist endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.exceptions import YTMusicServiceException
from app.schemas.playlist import PlaylistResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES
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
    response_model=PlaylistResponse,
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
        **COMMON_ERROR_RESPONSES
    }
)
async def get_playlist(
    playlist_id: str = Path(..., description="ID de la playlist (acepta browseId con prefijo VL)", examples={"example1": {"value": "PL..."}}),
    limit: int = Query(100, ge=1, le=5000, description="Número máximo de canciones"),
    start_index: int = Query(0, ge=0, description="Índice inicial para paginación"),
    related: bool = Query(False, description="Incluir canciones relacionadas"),
    suggestions_limit: int = Query(0, ge=0, le=50, description="Límite de sugerencias"),
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
    service: PlaylistService = Depends(get_playlist_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> PlaylistResponse:
    """
    Obtiene información completa de una playlist pública con paginación.
    
    - Acepta `playlistId` o `browseId` (con prefijo VL, se normaliza automáticamente)
    - `start_index`: Índice inicial para paginación (0 = desde el inicio)
    - `limit`: Número máximo de canciones a retornar
    - `prefetch_count`: Cuántos tracks enriquecer con stream URLs (default: 10, -1 = todos)
    
    Si `include_stream_urls=true` y `prefetch_count > 0`, los primeros N tracks incluyen:
    - `stream_url`: URL directa de audio (mejor calidad)
    """
    try:
        playlist_data = await service.get_playlist(
            playlist_id, 
            limit, 
            related, 
            suggestions_limit,
            start_index
        )
        
        # Apply limit/offset AFTER service returns
        if playlist_data.get('tracks'):
            tracks = playlist_data['tracks']
            if start_index > 0 and start_index < len(tracks):
                tracks = tracks[start_index:]
            if limit > 0 and limit < len(tracks):
                tracks = tracks[:limit]
            playlist_data['tracks'] = tracks
        
        # Enrich tracks with stream URLs
        if include_stream_urls and prefetch_count != 0 and playlist_data.get('tracks'):
            tracks = playlist_data['tracks']
            tracks_to_enrich = tracks if prefetch_count == -1 else tracks[:prefetch_count]
            tracks_remaining = [] if prefetch_count == -1 else tracks[prefetch_count:]
            
            if tracks_to_enrich:
                enriched_tracks = await stream_service.enrich_items_with_streams(
                    tracks_to_enrich, 
                    include_stream_urls=True
                )
                
                if tracks_remaining:
                    enriched_tracks.extend(tracks_remaining)
                
                playlist_data['tracks'] = enriched_tracks
                tracks_with_url = sum(1 for t in enriched_tracks if t.get('stream_url'))
                playlist_data['stream_urls_prefetched'] = tracks_with_url
                playlist_data['stream_urls_total'] = len(enriched_tracks)
        
        return playlist_data
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
