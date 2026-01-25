"""Browse endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.browse_service import BrowseService
from app.services.stream_service import StreamService

router = APIRouter(tags=["browse"])


def get_browse_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> BrowseService:
    """Dependency to get browse service."""
    return BrowseService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/home",
    summary="Get home page",
    description="Obtiene el contenido de la página principal de YouTube Music.",
    response_description="Contenido de la página principal",
    responses={200: {"description": "Contenido obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_home(
    service: BrowseService = Depends(get_browse_service)
) -> List[Dict[str, Any]]:
    """Obtiene el contenido de la página principal de YouTube Music."""
    try:
        return await service.get_home()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/artist/{channel_id}",
    summary="Get artist information",
    description="Obtiene información detallada de un artista incluyendo canciones populares, álbumes y más.",
    response_description="Información del artista",
    responses={200: {"description": "Artista obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_artist(
    channel_id: str = Query(..., description="ID del canal del artista", example="UC..."),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene información completa de un artista."""
    try:
        return await service.get_artist(channel_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/artist/{channel_id}/albums",
    summary="Get artist albums",
    description="Obtiene todos los álbumes de un artista.",
    response_description="Lista de álbumes del artista",
    responses={200: {"description": "Álbumes obtenidos exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_artist_albums(
    channel_id: str = Query(..., description="ID del canal del artista", example="UC..."),
    params: Optional[str] = Query(None, description="Parámetros de paginación"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene todos los álbumes de un artista."""
    try:
        return await service.get_artist_albums(channel_id, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/album/{album_id}",
    summary="Get album information",
    description="Obtiene información completa de un álbum incluyendo todas sus canciones.",
    response_description="Información del álbum con tracks",
    responses={
        200: {
            "description": "Álbum obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Album Title",
                        "artists": [{"name": "Artist"}],
                        "tracks": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Track Title",
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
async def get_album(
    album_id: str = Query(..., description="ID del álbum", example="MPREb..."),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para tracks"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene información completa de un álbum.
    
    Si `include_stream_urls=true`, cada track incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    try:
        album_data = await service.get_album(album_id)
        
        # Enrich tracks with stream URLs and thumbnails
        if include_stream_urls:
            # ytmusicapi returns tracks in different structures, check common ones
            tracks = album_data.get('tracks') or album_data.get('songs') or []
            if tracks:
                enriched_tracks = await stream_service.enrich_items_with_streams(
                    tracks, 
                    include_stream_urls=True
                )
                if 'tracks' in album_data:
                    album_data['tracks'] = enriched_tracks
                elif 'songs' in album_data:
                    album_data['songs'] = enriched_tracks
        
        return album_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/album/{album_id}/browse-id",
    summary="Get album browse ID",
    description="Obtiene el browse ID de un álbum a partir de su ID.",
    response_description="Browse ID del álbum",
    responses={200: {"description": "Browse ID obtenido exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_album_browse_id(
    album_id: str = Query(..., description="ID del álbum", example="MPREb..."),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, str]:
    """Obtiene el browse ID de un álbum."""
    try:
        browse_id = await service.get_album_browse_id(album_id)
        return {"browse_id": browse_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/song/{video_id}",
    summary="Get song metadata",
    description="Obtiene metadatos completos de una canción.",
    response_description="Metadatos de la canción",
    responses={200: {"description": "Canción obtenida exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_song(
    video_id: str = Query(..., description="ID del video/canción", example="rMbATaj7Il8"),
    signature_timestamp: Optional[int] = Query(None, description="Timestamp de firma (opcional)"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene metadatos completos de una canción."""
    try:
        return await service.get_song(video_id, signature_timestamp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/song/{video_id}/related",
    summary="Get related songs",
    description="Obtiene canciones relacionadas a una canción específica.",
    response_description="Lista de canciones relacionadas",
    responses={
        200: {
            "description": "Canciones relacionadas obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "videoId": "abc123",
                            "title": "Related Song",
                            "stream_url": "https://...",
                            "thumbnail": "https://..."
                        }
                    ]
                }
            }
        },
        500: {"description": "Error interno"}
    }
)
async def get_song_related(
    video_id: str = Query(..., description="ID del video/canción", example="rMbATaj7Il8"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> List[Dict[str, Any]]:
    """
    Obtiene canciones relacionadas a una canción.
    
    Si `include_stream_urls=true`, cada canción incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    try:
        related_songs = await service.get_song_related(video_id)
        
        # Enrich with stream URLs and thumbnails
        if include_stream_urls and related_songs:
            related_songs = await stream_service.enrich_items_with_streams(
                related_songs, 
                include_stream_urls=True
            )
        
        return related_songs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lyrics/{browse_id}",
    summary="Get song lyrics",
    description="Obtiene las letras de una canción usando su browse ID.",
    response_description="Letras de la canción",
    responses={200: {"description": "Letras obtenidas exitosamente"}, 500: {"description": "Error interno"}}
)
async def get_lyrics(
    browse_id: str = Query(..., description="Browse ID de la canción", example="MPAD..."),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene las letras de una canción."""
    try:
        return await service.get_lyrics(browse_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


