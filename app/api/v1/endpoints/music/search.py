"""Search endpoints."""
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from typing import Optional, Dict, Any, Union
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.validators import validate_search_query, validate_search_filter
from app.services.search_service import SearchService
from app.services.stream_service import StreamService
from app.schemas.search import (
    SearchResponse,
    SearchSuggestionsResponse,
    SearchSuggestionsDetailedResponse,
)
from app.schemas.errors import COMMON_ERROR_RESPONSES

router = APIRouter()


def get_search_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> SearchService:
    """Dependency to get search service."""
    return SearchService(ytmusic)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/",
    response_model=SearchResponse,
    summary="Search music content",
    description="Busca contenido musical en YouTube Music: canciones, videos, álbumes, artistas y playlists.",
    response_description="Resultados de búsqueda",
    responses={
        200: {
            "description": "Búsqueda exitosa",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Song Title",
                                "artists": [{"name": "Artist"}],
                                "album": {"name": "Album"},
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ],
                        "pagination": {
                            "page": 1,
                            "page_size": 10,
                            "total_results": 1,
                            "total_pages": 1,
                            "start_index": 0,
                            "end_index": 10,
                            "has_next": False,
                            "has_prev": False,
                        },
                        "query": "search query",
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
    limit: int = Query(10, ge=1, le=50, description="Número de resultados"),
    start_index: int = Query(0, ge=0, description="Índice inicial para paginación"),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Items por página"),
    ignore_spelling: bool = Query(False, description="Ignorar sugerencias de ortografía"),
    include_stream_urls: bool = Query(
        True, 
        description="Incluir stream URLs y mejores thumbnails para songs/videos"
    ),
    service: SearchService = Depends(get_search_service),
    stream_service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Busca contenido musical en YouTube Music con paginación estandarizada.
    
    **Filtros disponibles:**
    - `songs`: Solo canciones
    - `videos`: Solo videos
    - `albums`: Solo álbumes
    - `artists`: Solo artistas
    - `playlists`: Solo playlists
    
    **Paginación:**
    - `page`: Número de página (1 = primera página)
    - `page_size`: Items por página (default 10, máximo 50)
    - `start_index`: Índice inicial (legacy, mantener compatibilidad)
    - `limit`: Número de resultados (legacy)
    
    Si `filter` es `songs` o `videos` y `include_stream_urls=true`, cada resultado incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    # Validate inputs
    q = validate_search_query(q)
    filter = validate_search_filter(filter)

    # Search - exceptions handled by global handlers
    result = await service.search(
        query=q,
        filter=filter,
        scope=scope,
        limit=limit,
        ignore_spelling=ignore_spelling,
        start_index=start_index,
        page=page,
        page_size=page_size
    )

    # Enrich songs/videos with stream URLs and thumbnails
    # Only attempt enrichment if there are items with videoId
    if include_stream_urls:
        try:
            items = result.get('items', [])
            # Filter items that have videoId - artists/albums/playlists don't have videoId
            # We check each item for videoId regardless of filter type for robustness
            items_to_enrich = [r for r in items if isinstance(r, dict) and (r.get('videoId') or r.get('video_id'))]
            
            if items_to_enrich:
                enriched_items = await stream_service.enrich_items_with_streams(
                    items_to_enrich,
                    include_stream_urls=True
                )
                
                # Create a map of videoId to enriched item for quick lookup
                enriched_map = {}
                for item in enriched_items:
                    vid = item.get('videoId') or item.get('video_id')
                    if vid:
                        enriched_map[vid] = item
                
                # Update the original results list preserving order
                for i in range(len(items)):
                    item = items[i]
                    if not isinstance(item, dict):
                        continue
                    
                    vid = item.get('videoId') or item.get('video_id')
                    if vid and vid in enriched_map:
                        # Merge enriched data (especially stream_url) into the original item
                        items[i].update(enriched_map[vid])
                
                result['items'] = items
        except Exception as enrich_error:
            # Log but don't fail the whole request if enrichment fails
            import logging
            logging.getLogger(__name__).warning(f"Stream enrichment failed: {enrich_error}")

    result['query'] = q
    return result


@router.get(
    "/suggestions",
    response_model=Union[SearchSuggestionsResponse, SearchSuggestionsDetailedResponse],
    summary="Get search suggestions",
    description=(
        "Sugerencias de búsqueda (ytmusicapi get_search_suggestions). "
        "Usa detailed=true para el formato requerido por DELETE /suggestions con suggestions+indices."
    ),
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
    detailed: bool = Query(
        False,
        description="Si true, devuelve objetos dict (detailed_runs=True) como en la documentación de ytmusicapi",
    ),
    service: SearchService = Depends(get_search_service),
) -> Union[SearchSuggestionsResponse, SearchSuggestionsDetailedResponse]:
    """
    Obtiene sugerencias de búsqueda para autocompletado.

    **Códigos de error:**
    - `VALIDATION_ERROR` (400): Query vacío
    - `EXTERNAL_SERVICE_ERROR` (502): Error de YouTube Music
    """
    q = validate_search_query(q)
    raw = await service.get_search_suggestions(q, detailed_runs=detailed)
    if detailed:
        if not all(isinstance(x, dict) for x in raw):
            raise HTTPException(
                status_code=502,
                detail="Formato inesperado de sugerencias detalladas",
            )
        return SearchSuggestionsDetailedResponse(suggestions=raw)
    return SearchSuggestionsResponse(suggestions=raw)



