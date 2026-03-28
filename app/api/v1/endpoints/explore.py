"""Explore endpoints - Public content: charts, moods, genres."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, Dict, Any, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.core.exceptions import YTMusicServiceException
from app.schemas.explore import ExploreResponse, MoodCategoriesResponse, MoodPlaylistsResponse, ChartsResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.services.explore_service import ExploreService
from app.services.stream_service import StreamService

router = APIRouter(tags=["explore"])


async def _enrich_home_with_streams(home: List[Dict[str, Any]], stream_service: StreamService) -> List[Dict[str, Any]]:
    """
    Enrich home content (Quick picks, playlists, albums) with stream URLs.
    
    Args:
        home: List of home sections
        stream_service: Service to get stream URLs
        
    Returns:
        Home content with stream URLs added to playable items
    """
    enriched_home = []
    
    for section in home:
        section_title = section.get('title', '')
        contents = section.get('contents', [])
        
        if not contents:
            enriched_home.append(section)
            continue
        
        # Only process sections with playable content (songs, playlists)
        # Skip sections that don't have playable items
        if not isinstance(contents, list):
            enriched_home.append(section)
            continue
        
        # Check if items have videoId (songs) or playlistId/albums
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


def get_explore_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> ExploreService:
    """Dependency to get explore service."""
    return ExploreService(ytmusic)


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="Get explore content",
    description="Obtiene contenido de exploración: moods, géneros, charts y home. Incluye top songs y trending con stream URLs opcionales.",
    response_description="Contenido de exploración con moods, géneros y charts",
    responses={
        200: {
            "description": "Contenido de exploración obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "moods_genres": [
                            {"title": "Cumbia", "params": "ggMPOg1uX3hRRFdlaEhHU09k"}
                        ],
                        "home": [],
                        "charts": {
                            "top_songs": [
                                {
                                    "videoId": "rMbATaj7Il8",
                                    "title": "Song Title",
                                    "artists": [{"name": "Artist"}],
                                    "stream_url": "https://...",
                                    "thumbnail": "https://..."
                                }
                            ],
                            "trending": []
                        }
                    }
                }
            }
        },
        500: {"description": "Error interno del servidor"}
    }
)
async def explore_music(
    include_stream_urls: bool = Query(
        False, 
        description="Incluir stream URLs y mejores thumbnails para charts"
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=50, 
        description="Número máximo de canciones en charts"
    ),
    start_index: int = Query(
        0, 
        ge=0, 
        description="Índice inicial para paginación de charts"
    ),
    prefetch_count: int = Query(
        10, 
        ge=-1, 
        le=50, 
        description="Número de URLs a obtener en paralelo (0=none, -1=todas)"
    ),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene contenido completo de exploración.
    
    - **moods_genres**: Categorías de moods/géneros con sus `params` para obtener playlists
    - **home**: Contenido de la página principal de YouTube Music
    - **charts**: Top songs y trending con paginación y stream_url si include_stream_urls=true
    
    **Paginación de charts:**
    - `limit`: Número de canciones a retornar (default: 10, max: 50)
    - `start_index`: Índice inicial para paginación
    - `prefetch_count`: Cuántos tracks enriquecer con stream URLs (default: 10, -1=todos)
    
    Cada categoría en `moods_genres` tiene un campo `params` que puedes usar en `/explore/moods/{params}`.
    """
    import logging
    
    logger = logging.getLogger("explore")
    
    try:
        home_data = await service.get_home_with_moods()
    except YTMusicServiceException:
        raise
    except Exception as e:
        logger.warning(f"Failed to get home with moods: {e}")
        home_data = {"home": [], "moods": []}
    
    top_songs_data = []
    trending_data = []
    try:
        charts = await service.get_charts()
        
        top_songs_data = charts.get('top_songs', [])
        if not top_songs_data:
            top_songs_data = charts.get('videos', [])
        
        trending_data = charts.get('trending', [])
        if not trending_data:
            trending_data = top_songs_data
        
        # Initialize stats for response
        top_songs_with_url = 0
        trending_with_url = 0
        
        # Apply pagination BEFORE enrichment (same pattern as playlists)
        if start_index > 0 and start_index < len(top_songs_data):
            top_songs_data = top_songs_data[start_index:]
        if limit > 0 and limit < len(top_songs_data):
            top_songs_data = top_songs_data[:limit]
        
        if start_index > 0 and start_index < len(trending_data):
            trending_data = trending_data[start_index:]
        if limit > 0 and limit < len(trending_data):
            trending_data = trending_data[:limit]
        
        # Enrich only prefetch_count items with stream URLs
        if include_stream_urls:
            from app.services.stream_service import StreamService
            stream_service = StreamService()
            
            if top_songs_data:
                top_to_enrich = top_songs_data if prefetch_count == -1 else top_songs_data[:prefetch_count]
                top_remaining = [] if prefetch_count == -1 else top_songs_data[prefetch_count:]
                
                if top_to_enrich:
                    top_songs_data = await stream_service.enrich_items_with_streams(
                        top_to_enrich,
                        include_stream_urls=True
                    )
                    if top_remaining:
                        top_songs_data.extend(top_remaining)
            
            if trending_data:
                trending_to_enrich = trending_data if prefetch_count == -1 else trending_data[:prefetch_count]
                trending_remaining = [] if prefetch_count == -1 else trending_data[prefetch_count:]
                
                if trending_to_enrich:
                    trending_data = await stream_service.enrich_items_with_streams(
                        trending_to_enrich, 
                        include_stream_urls=True
                    )
                    if trending_remaining:
                        trending_data.extend(trending_remaining)
        
        # Calculate stream URL stats for response
        top_songs_with_url = sum(1 for t in top_songs_data if t.get('stream_url'))
        trending_with_url = sum(1 for t in trending_data if t.get('stream_url'))
    except YTMusicServiceException:
        raise
    except Exception as e:
        logger.warning(f"Failed to get charts (non-critical): {e}")
    
    # Enrich home content with stream URLs
    home = home_data.get("home", [])
    if include_stream_urls and home:
        logger.info(f"Enriching home with {len(home)} sections")
        stream_service = StreamService()
        try:
            home = await _enrich_home_with_streams(home, stream_service)
            logger.info(f"Home enrichment complete")
        except YTMusicServiceException:
            raise
        except Exception as e:
            logger.error(f"Error enriching home: {e}")
    
    # Si no hay moods ni home ni charts, entonces sí es un error real
    moods_genres = home_data.get("moods", [])
    if not moods_genres and not home and not top_songs_data:
        raise HTTPException(
            status_code=500, 
            detail="No se pudo obtener contenido de exploración. YouTube Music no responde."
        )
    
    response = {
        "moods_genres": moods_genres,
        "home": home,
        "charts": {
            "top_songs": top_songs_data,
            "trending": trending_data,
            "pagination": {
                "limit": limit,
                "start_index": start_index,
                "prefetch_count": prefetch_count
            },
            "stream_urls_prefetched": top_songs_with_url,
            "stream_urls_total": len(top_songs_data)
        },
        "info": {
            "usage": "Cada categoría en 'moods_genres' tiene un campo 'params'. Usa ese 'params' en /explore/moods/{params} para obtener las playlists de esa categoría.",
            "charts_usage": "Las canciones en 'charts' incluyen 'stream_url' y 'thumbnail' (mejor calidad) si include_stream_urls=true. Usa limit/start_index para paginación."
        }
    }
    
    return response


@router.get(
    "/moods",
    response_model=Dict[str, Any],
    summary="Get mood categories",
    description="Obtiene todas las categorías de moods y géneros disponibles en YouTube Music.",
    response_description="Categorías organizadas por secciones",
    responses={
        200: {
            "description": "Categorías obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "categories": {
                            "For you": [
                                {"params": "ggMPOg1uX1ZwN0pHT2NBT1Fk", "title": "1980s"}
                            ],
                            "Genres": [
                                {"params": "ggMPOg1uX3hRRFdlaEhHU09k", "title": "Cumbia"}
                            ],
                            "Moods & moments": [
                                {"params": "ggMPOg1uXzVuc0dnZlhpV3Ba", "title": "Chill"}
                            ]
                        }
                    }
                }
            }
        },
        500: {"description": "Error interno del servidor"}
    }
)
async def get_mood_categories(
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene todas las categorías de moods y géneros.
    
    Retorna un diccionario con secciones:
    - **For you**: Categorías personalizadas
    - **Genres**: Géneros musicales
    - **Moods & moments**: Estados de ánimo y momentos
    
    Cada categoría tiene:
    - `params`: Usar en `/explore/moods/{params}` para obtener playlists
    - `title`: Nombre de la categoría
    """
    try:
        categories = await service.get_mood_categories()
        return {
            "categories": categories,
            "structure": "Las categorías están organizadas en secciones: 'For you', 'Genres', 'Moods & moments'"
        }
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/moods/{params}",
    response_model=Dict[str, Any],
    summary="Get mood/genre playlists",
    description="Obtiene playlists de una categoría de mood o género usando sus parámetros codificados.",
    response_description="Lista de playlists de la categoría",
    responses={
        200: {
            "description": "Playlists obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "playlists": [
                            {"title": "Cumbia Mix", "playlistId": "PL123"}
                        ]
                    }
                }
            }
        },
        404: {"description": "Categoría no encontrada (params inválidos)"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_mood_playlists(
    params: str = Path(..., description="Parámetros codificados de la categoría", examples={"example1": {"value": "ggMPOg1uX3hRRFdlaEhHU09k"}}),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene playlists de una categoría de mood o género.
    
    Usa los `params` de una categoría obtenida en `/explore/moods` o `/explore`.
    Los params son valores codificados como `ggMPOg1uX1JOQWZFeDByc2Jm`.
    """
    try:
        result = await service.get_mood_playlists(params)
        return {
            "playlists": result
        }
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/charts",
    response_model=Dict[str, Any],
    summary="Get music charts",
    description="Obtiene los charts de YouTube Music: top songs y trending. Opcionalmente incluye stream URLs.",
    response_description="Charts con top songs y trending",
    responses={
        200: {
            "description": "Charts obtenidos exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "top_songs": [
                            {
                                "videoId": "rMbATaj7Il8",
                                "title": "Top Song",
                                "artists": [{"name": "Artist"}],
                                "stream_url": "https://...",
                                "thumbnail": "https://..."
                            }
                        ],
                        "trending": [],
                        "country": "global"
                    }
                }
            }
        },
        500: {"description": "Error interno del servidor"}
    }
)
async def get_charts(
    country: Optional[str] = Query(
        None, 
        description="Código de país ISO 3166-1 Alpha-2 (ej: 'US', 'PE'). Default: global"
    ),
    include_stream_urls: bool = Query(
        False, 
        description="Incluir stream URLs y mejores thumbnails"
    ),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene charts de YouTube Music.
    
    - **top_songs**: Canciones más populares
    - **trending**: Canciones en tendencia
    - **country**: País de los charts (o 'global')
    
    Si `include_stream_urls=true`, cada canción incluye:
    - `stream_url`: URL directa de audio (mejor calidad)
    - `thumbnail`: URL de thumbnail en mejor calidad
    """
    try:
        charts = await service.get_charts(country)
        
        top_songs_data = charts.get('top_songs', [])
        if not top_songs_data:
            top_songs_data = charts.get('videos', [])
        
        trending_data = charts.get('trending', [])
        if not trending_data:
            trending_data = top_songs_data
        
        # Enrich with stream URLs and thumbnails
        if include_stream_urls:
            from app.services.stream_service import StreamService
            stream_service = StreamService()
            
            # Enrich top_songs
            if top_songs_data:
                top_songs_data = await stream_service.enrich_items_with_streams(
                    top_songs_data, 
                    include_stream_urls=True
                )
            
            # Enrich trending
            if trending_data:
                trending_data = await stream_service.enrich_items_with_streams(
                    trending_data, 
                    include_stream_urls=True
                )
        
        response = {
            "top_songs": top_songs_data,
            "trending": trending_data,
            "country": country or "global"
        }
        
        return response
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/category/{category_params}",
    response_model=Dict[str, Any],
    summary="Get category playlists (alias)",
    description="Alias para `/explore/moods/{params}`. Obtiene playlists de una categoría.",
    response_description="Lista de playlists de la categoría",
    responses={200: {"description": "Playlists obtenidas exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_category(
    category_params: str = Path(..., description="Params de la categoría", examples={"example1": {"value": "ggMPOg1uX3hRRFdlaEhHU09k"}}),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene playlists de una categoría (alias de `/explore/moods/{params}`).
    
    Usa el `params` de una categoría de mood/género para obtener sus playlists.
    """
    try:
        result = await service.get_mood_playlists(category_params)
        return {
            "playlists": result
        }
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando categoría: {str(e)}")
