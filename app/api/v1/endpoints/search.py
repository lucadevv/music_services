"""Search endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.validators import validate_search_query, validate_search_filter
from app.services.search_service import SearchService
from app.services.stream_service import StreamService
from app.schemas.errors import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["search"])


def get_search_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> SearchService:
    """Dependency to get search service."""
    return SearchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/",
    summary="Search music content",
    description="Busca contenido musical en YouTube Music: canciones, videos, álbumes, artistas y playlists.",
    response_description="Resultados de búsqueda",
    responses={
        200: {
            "description": "Búsqueda exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Song Title",
                                "artists": [{"name": "Artist"}],
                                "album": {"name": "Album"},
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ],
                        "query": "search query"
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def search_music(
    q: str = Query(..., description="Query de búsqueda", examples=["cumbia peruana"]),
    filter: Optional[str] = Query(
        None, 
        description="Filtro: songs, videos, albums, artists, playlists",
        examples=["songs"]
    ),
    scope: Optional[str] = Query(None, description="Scope de búsqueda"),
    limit: int = Query(20, ge=1, le=50, description="Número de resultados", examples=[20]),
    ignore_spelling: bool = Query(False, description="Ignorar sugerencias de ortografía"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para songs/videos"
    ),
    service: SearchService = Depends(get_search_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Busca contenido musical en YouTube Music.
    
    **Filtros disponibles:**
    - `songs`: Solo canciones
    - `videos`: Solo videos
    - `albums`: Solo álbumes
    - `artists`: Solo artistas
    - `playlists`: Solo playlists
    
    Si `filter` es `songs` o `videos` y `include_stream_urls=true`, cada resultado incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    
    **Códigos de error:**
    - `VALIDATION_ERROR` (400): Query vacío o filtro inválido
    - `AUTHENTICATION_ERROR` (401): Error de autenticación
    - `RATE_LIMIT_ERROR` (429): Rate limit excedido
    - `EXTERNAL_SERVICE_ERROR` (502): Error de YouTube Music
    """
    # Validate inputs
    q = validate_search_query(q)
    filter = validate_search_filter(filter)
    
    # Search - exceptions handled by global handlers
    results = await service.search(q, filter, scope, limit, ignore_spelling)
    
    # Enrich songs/videos with stream URLs and thumbnails
    if include_stream_urls and filter in ['songs', 'videos', None]:
        # Filter items that have videoId
        items_to_enrich = [r for r in results if r.get('videoId')]
        if items_to_enrich:
            enriched_items = await stream_service.enrich_items_with_streams(
                items_to_enrich, 
                include_stream_urls=True
            )
            # Map enriched items back to results - preserve ALL original fields
            enriched_map = {item.get('videoId'): item for item in enriched_items if item.get('videoId')}
            for i, result in enumerate(results):
                video_id = result.get('videoId')
                if video_id and video_id in enriched_map:
                    # enriched_map contains ALL original fields + stream_url + thumbnail
                    # Replace the entire result with the enriched version (which has all fields)
                    results[i] = enriched_map[video_id]
    
    return {"results": results, "query": q}


@router.get(
    "/suggestions",
    summary="Get search suggestions",
    description="Obtiene sugerencias de búsqueda basadas en el query parcial.",
    response_description="Lista de sugerencias",
    responses={
        200: {
            "description": "Sugerencias obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "suggestions": ["cumbia peruana", "cumbia colombiana", "cumbia villera"]
                    }
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_search_suggestions(
    q: str = Query(..., description="Query parcial para obtener sugerencias", examples=["cumb"]),
    service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """
    Obtiene sugerencias de búsqueda para autocompletado.
    
    **Códigos de error:**
    - `VALIDATION_ERROR` (400): Query vacío
    - `EXTERNAL_SERVICE_ERROR` (502): Error de YouTube Music
    """
    # Validate query
    q = validate_search_query(q)
    
    # Get suggestions - exceptions handled by global handlers
    suggestions = await service.get_search_suggestions(q)
    return {"suggestions": suggestions}


@router.delete(
    "/suggestions",
    summary="Remove search suggestions",
    description="Elimina una sugerencia de búsqueda del historial.",
    response_description="Resultado de la eliminación",
    responses={
        200: {
            "description": "Sugerencia eliminada exitosamente",
            "content": {
                "application/json": {
                    "example": {"success": True}
                }
            }
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def remove_search_suggestions(
    q: str = Query(..., description="Query a eliminar de las sugerencias", examples=["cumbia"]),
    service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """
    Elimina una sugerencia de búsqueda del historial.
    
    **Códigos de error:**
    - `VALIDATION_ERROR` (400): Query vacío
    - `AUTHENTICATION_ERROR` (401): Requiere autenticación
    - `EXTERNAL_SERVICE_ERROR` (502): Error de YouTube Music
    """
    # Validate query
    q = validate_search_query(q)
    
    # Remove suggestion - exceptions handled by global handlers
    result = await service.remove_search_suggestions(q)
    return {"success": result}
