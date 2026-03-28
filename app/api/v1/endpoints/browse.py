"""Browse endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.exceptions import YTMusicServiceException
from app.schemas.browse import (
    ArtistAlbumsResponse,
    ArtistResponse,
    AlbumResponse,
    HomeResponse,
    LyricsResponse,
    SongResponse,
    AlbumBrowseIdResponse,
    RelatedSongsResponse,
)
from app.schemas.errors import COMMON_ERROR_RESPONSES
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
    response_model=HomeResponse,
    summary="Get home page",
    description="Obtiene el contenido de la página principal de YouTube Music.",
    response_description="Contenido de la página principal",
    responses={200: {"description": "Contenido obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_home(
    service: BrowseService = Depends(get_browse_service)
) -> List[Dict[str, Any]]:
    """Obtiene el contenido de la página principal de YouTube Music."""
    try:
        result = await service.get_home()
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get(
    "/artist/{channel_id}/albums",
    response_model=ArtistAlbumsResponse,
    summary="Get artist albums",
    description="Obtiene todos los álbumes de un artista.",
    response_description="Lista de álbumes del artista",
    responses={200: {"description": "Álbumes obtenidos exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_artist_albums(
    channel_id: str = Path(..., description="ID del canal del artista", examples={"example1": {"value": "UC..."}}),
    params: Optional[str] = Query(None, description="Parámetros de paginación"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene todos los álbumes de un artista."""
    try:
        result = await service.get_artist_albums(channel_id, params)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/album/{album_id}",
    response_model=AlbumResponse,
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
        **COMMON_ERROR_RESPONSES
    }
)
async def get_album(
    album_id: str = Path(..., description="ID del álbum", examples={"example1": {"value": "MPREb..."}}),
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
        
        if include_stream_urls:
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
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/album/{album_id}/browse-id",
    response_model=AlbumBrowseIdResponse,
    summary="Get album browse ID",
    description="Obtiene el browse ID de un álbum a partir de su ID.",
    response_description="Browse ID del álbum",
    responses={200: {"description": "Browse ID obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_album_browse_id(
    album_id: str = Path(..., description="ID del álbum", examples={"example1": {"value": "MPREb..."}}),
    service: BrowseService = Depends(get_browse_service)
) -> AlbumBrowseIdResponse:
    """Obtiene el browse ID de un álbum."""
    try:
        browse_id = await service.get_album_browse_id(album_id)
        return AlbumBrowseIdResponse(browse_id=browse_id)
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/song/{video_id}",
    response_model=SongResponse,
    summary="Get song metadata",
    description="Obtiene metadatos completos de una canción.",
    response_description="Metadatos de la canción",
    responses={200: {"description": "Canción obtenida exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_song(
    video_id: str = Path(..., description="ID del video/canción", examples={"example1": {"value": "rMbATaj7Il8"}}),
    signature_timestamp: Optional[int] = Query(None, description="Timestamp de firma (opcional)"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene metadatos completos de una canción."""
    try:
        result = await service.get_song(video_id, signature_timestamp)
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/song/{video_id}/related",
    response_model=RelatedSongsResponse,
    summary="Get related songs",
    description="Obtiene canciones relacionadas a una canción específica.",
    response_description="Lista de canciones relacionadas",
    responses={
        200: {
            "description": "Canciones relacionadas obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "songs": [
                            {
                                "videoId": "abc123",
                                "title": "Related Song",
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ],
                        "count": 10
                    }
                }
            }
        },
        500: {"description": "Error interno"},
        502: {"description": "Bad Gateway"},
        404: {"description": "No encontrado"},
        **COMMON_ERROR_RESPONSES
    }
)
async def get_song_related(
    video_id: str = Path(..., description="ID del video/canción", examples={"example1": {"value": "rMbATaj7Il8"}}),
    include_stream_urls: bool = Query(
        False, 
        description="Incluir stream URLs y mejores thumbnails"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> RelatedSongsResponse:
    """
    Obtiene canciones relacionadas a una canción.
    
    Si `include_stream_urls=true`, cada canción incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    from app.core.exceptions import ExternalServiceError, ResourceNotFoundError
    
    try:
        related_songs = await service.get_song_related(video_id)
        # Ensure we always return a list, even if service returns None
        if related_songs is None:
            related_songs = []
        
        if include_stream_urls and related_songs:
            related_songs = await stream_service.enrich_items_with_streams(
                related_songs, 
                include_stream_urls=True
            )
        
        return RelatedSongsResponse(songs=related_songs, count=len(related_songs))
    except YTMusicServiceException:
        raise
    except Exception as e:
        # Check if this looks like a YouTube API error that should return 502
        error_str = str(e).lower()
        if ("internal server error" in error_str or 
            "500" in error_str or 
            "youtube" in error_str or
            "gate" in error_str or
            "bad gateway" in error_str or
            "502" in error_str):
            raise ExternalServiceError(
                message="Error en YouTube Music durante obtener canciones relacionadas. Intenta más tarde.",
                details={"operation": "obtener canciones relacionadas", "service": "YouTube Music"}
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lyrics/{browse_id}",
    response_model=LyricsResponse,
    summary="Get song lyrics",
    description="Obtiene las letras de una canción usando su browse ID.",
    response_description="Letras de la canción",
    responses={200: {"description": "Letras obtenidas exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_lyrics(
    browse_id: str = Path(..., description="Browse ID de la canción", examples={"example1": {"value": "MPAD..."}}),
    service: BrowseService = Depends(get_browse_service)
) -> LyricsResponse:
    """Obtiene las letras de una canción."""
    try:
        result = await service.get_lyrics(browse_id)
        return LyricsResponse(**result) if isinstance(result, dict) else result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lyrics-by-video/{video_id}",
    response_model=LyricsResponse,
    summary="Get song lyrics by video ID",
    description="Obtiene las letras de una canción usando su video ID.",
    response_description="Letras de la canción",
    responses={200: {"description": "Letras obtenidas exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_lyrics_by_video(
    video_id: str = Path(..., description="Video ID de YouTube", examples={"example1": {"value": "dQw4w9WgXcQ"}}),
    service: BrowseService = Depends(get_browse_service)
) -> LyricsResponse:
    """Obtiene las letras de una canción por su video ID."""
    try:
        result = await service.get_lyrics_by_video_id(video_id)
        return LyricsResponse(**result) if isinstance(result, dict) else result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


