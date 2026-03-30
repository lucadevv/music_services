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

router = APIRouter()


def get_browse_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> BrowseService:
    """Dependency to get browse service."""
    return BrowseService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


async def _enrich_home_with_streams(home_items: List[Dict[str, Any]], stream_service: StreamService) -> List[Dict[str, Any]]:
    """
    Enrich home content (Quick picks, playlists, albums) with stream URLs.
    """
    enriched_home = []
    
    for section in home_items:
        contents = section.get('contents', [])
        
        if not contents or not isinstance(contents, list):
            enriched_home.append(section)
            continue
        
        # Check if items have videoId (songs)
        has_songs = any(item.get('videoId') for item in contents if isinstance(item, dict))
        
        if has_songs:
            # Enrich songs with stream URLs
            enriched_contents = await stream_service.enrich_items_with_streams(
                contents,
                include_stream_urls=True
            )
            section = {**section, 'contents': enriched_contents}
        
        enriched_home.append(section)
    
    return enriched_home


@router.get(
    "/home",
    response_model=HomeResponse,
    summary="Get home page",
    description="Obtiene el contenido de la página principal de YouTube Music con paginación.",
    response_description="Contenido paginado de la página principal",
    responses={200: {"description": "Contenido obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_home(
    limit: int = Query(20, ge=1, le=50, description="Número de secciones a obtener"),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Items por página (máximo 50)"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para secciones de canciones"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """Obtiene el contenido de la página principal con paginación."""
    result = await service.get_home(
        limit=limit,
        page=page,
        page_size=page_size
    )

    if include_stream_urls and result.get('items'):
        result['items'] = await _enrich_home_with_streams(result['items'], stream_service)

    return result


@router.get(
    "/artist/{channel_id}",
    response_model=ArtistResponse,
    summary="Get artist information",
    description="Obtiene información completa de un artista: metadatos, álbumes y canciones populares.",
    response_description="Información detallada del artista",
    responses={200: {"description": "Artista obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_artist(
    channel_id: str = Path(..., description="ID del canal del artista", examples={"example1": {"value": "UC..."}}),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs para las canciones populares del artista"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """Obtiene información de un artista."""
    artist_data = await service.get_artist(channel_id)
    
    if include_stream_urls:
        # Los artistas suelen tener una sección de 'songs' o 'top_songs'
        songs = artist_data.get('songs', {}).get('results', [])
        if songs:
            enriched_songs = await stream_service.enrich_items_with_streams(
                songs,
                include_stream_urls=True
            )
            artist_data['songs']['results'] = enriched_songs
            
    return artist_data


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
    return await service.get_artist_albums(channel_id, params)


@router.get(
    "/album/{album_id}",
    response_model=AlbumResponse,
    summary="Get album information",
    description="Obtiene información completa de un álbum con paginación para tracks.",
    response_description="Información del álbum con tracks paginados",
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
                        ],
                        "pagination": {
                            "total_results": 45,
                            "total_pages": 5,
                            "page": 1,
                            "page_size": 10,
                            "has_next": True,
                            "has_prev": False
                        }
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_album(
    album_id: str = Path(..., description="ID del álbum", examples={"example1": {"value": "MPREb..."}}),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Tracks por página (máximo 50)"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para tracks"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene información completa de un álbum con tracks paginados.
    
    Si `include_stream_urls=true`, cada track incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    album_data = await service.get_album(
        album_id=album_id,
        page=page,
        page_size=page_size
    )

    if include_stream_urls:
        tracks = album_data.get('items') or album_data.get('tracks') or album_data.get('songs') or []
        if tracks:
            enriched_tracks = await stream_service.enrich_items_with_streams(
                tracks,
                include_stream_urls=True
            )
            album_data['items'] = enriched_tracks

    return album_data


@router.get(
    "/album/{album_id}/browse-id",
    summary="Get album browse ID",
    description="Obtiene el browse ID de un álbum a partir de su ID.",
    response_description="Browse ID del álbum",
    responses={200: {"description": "Browse ID obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_album_browse_id(
    album_id: str = Path(..., description="ID del álbum", examples={"example1": {"value": "MPREb..."}}),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene el browse ID de un álbum."""
    browse_id = await service.get_album_browse_id(album_id)
    if browse_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Álbum no encontrado: {album_id}"
        )
    # Retornar como dict con browseId (camelCase para consistencia)
    return {"browseId": browse_id}


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
    from app.services.response_service import ResponseService
    from app.core.exceptions import ExternalServiceError
    
    result = await service.get_song(video_id, signature_timestamp)
    
    # Si el resultado no es un dict, retornar error 502
    if not isinstance(result, dict):
        raise ExternalServiceError(
            message=f"YouTube Music retornó una respuesta inesperada para el video {video_id}",
            details={"response_type": type(result).__name__ if result else "empty", "video_id": video_id}
        )
    
    # Normalizar respuesta cruda del player de YouTube
    try:
        normalized = ResponseService.normalize_song_player_response(result)
        return normalized
    except (ValueError, AttributeError, TypeError) as norm_error:
        # Si falla la normalización, retornar los datos crudos pero en formato dict
        raise ExternalServiceError(
            message=f"Video no disponible o información incompleta: {video_id}",
            details={"video_id": video_id, "normalization_error": str(norm_error), "error_type": type(norm_error).__name__}
        )


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
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Canciones por página (máximo 50)"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails"
    ),
    service: BrowseService = Depends(get_browse_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene canciones relacionadas con paginación.
    
    Si `include_stream_urls=true`, cada canción incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    result = await service.get_song_related(
        video_id=video_id,
        page=page,
        page_size=page_size
    )

    if include_stream_urls and result.get('items'):
        result['items'] = await stream_service.enrich_items_with_streams(
            result['items'],
            include_stream_urls=True
        )

    return result


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
    result = await service.get_lyrics(browse_id)
    return LyricsResponse(**result) if isinstance(result, dict) else result


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
    result = await service.get_lyrics_by_video_id(video_id)
    return LyricsResponse(**result) if isinstance(result, dict) else result


