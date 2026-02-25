"""Explore endpoints - Public content: charts, moods, genres."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import Optional, Dict, Any, List
from ytmusicapi import YTMusic

from app.core.ytmusic_client import get_ytmusic
from app.services.explore_service import ExploreService

router = APIRouter(tags=["explore"])


def get_explore_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> ExploreService:
    """Dependency to get explore service."""
    return ExploreService(ytmusic)


@router.get(
    "/",
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
        True, 
        description="Incluir stream URLs y mejores thumbnails para charts"
    ),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene contenido completo de exploración.
    
    - **moods_genres**: Categorías de moods/géneros con sus `params` para obtener playlists
    - **home**: Contenido de la página principal de YouTube Music
    - **charts**: Top songs y trending con `stream_url` y `thumbnail` si `include_stream_urls=true`
    
    Cada categoría en `moods_genres` tiene un campo `params` que puedes usar en `/explore/moods/{params}`.
    """
    try:
        # Get home with moods
        home_data = await service.get_home_with_moods()
        
        # Get charts
        charts = await service.get_charts()
        
        # Adapt charts response
        top_songs_data = charts.get('top_songs', [])
        if not top_songs_data:
            top_songs_data = charts.get('videos', [])
        
        trending_data = charts.get('trending', [])
        if not trending_data:
            trending_data = top_songs_data
        
        # Enrich charts with stream URLs and thumbnails
        if include_stream_urls:
            from app.services.stream_service import StreamService
            stream_service = StreamService()
            
            if top_songs_data:
                top_songs_data = await stream_service.enrich_items_with_streams(
                    top_songs_data, 
                    include_stream_urls=True
                )
            
            if trending_data:
                trending_data = await stream_service.enrich_items_with_streams(
                    trending_data, 
                    include_stream_urls=True
                )
        
        return {
            "moods_genres": home_data.get("moods", []),
            "home": home_data.get("home", []),
            "charts": {
                "top_songs": top_songs_data,
                "trending": trending_data
            },
            "info": {
                "usage": "Cada categoría en 'moods_genres' tiene un campo 'params'. Usa ese 'params' en /explore/moods/{params} para obtener las playlists de esa categoría.",
                "charts_usage": "Las canciones en 'charts' incluyen 'stream_url' y 'thumbnail' (mejor calidad) si include_stream_urls=true."
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/moods",
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/moods/{params}",
    summary="Get playlists by mood/genre",
    description="Obtiene playlists de un mood o género específico usando el `params` de una categoría.",
    response_description="Lista de playlists del mood/género",
    responses={
        200: {
            "description": "Playlists obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "playlists": [
                            {
                                "playlistId": "PL...",
                                "title": "Best Cumbia Songs",
                                "thumbnails": [{"url": "https://..."}]
                            }
                        ],
                        "method": "direct"
                    }
                }
            }
        },
        500: {"description": "Error al obtener playlists"}
    }
)
async def get_mood_playlists(
    params: str = Path(..., description="Params obtenido de una categoría de mood/género", examples={"example1": {"value": "ggMPOg1uX3hRRFdlaEhHU09k"}}),
    genre_name: Optional[str] = Query(
        None, 
        description="Nombre del género (fallback si get_mood_playlists falla)"
    ),
    use_search: bool = Query(
        False, 
        description="Forzar uso de búsqueda alternativa en lugar de get_mood_playlists"
    ),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """
    Obtiene playlists de un mood o género usando `params`.
    
    - Usa el `params` de una categoría obtenida en `/explore/moods`
    - Cada playlist retornada tiene un `playlistId` para usar en `/api/v1/playlists/{playlistId}`
    - Si `get_mood_playlists()` falla, se usa automáticamente búsqueda alternativa
    - Puedes forzar búsqueda con `?use_search=true`
    """
    # Si se fuerza búsqueda o no hay params válido, usar búsqueda directamente
    if use_search or not params:
        if not genre_name:
            genre_name = await service.get_genre_name_from_params(params) or "music"
        
        try:
            results = await service.get_mood_playlists_alternative(genre_name)
            return {
                "playlists": results,
                "method": "search",
                "genre_name": genre_name
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error en búsqueda alternativa: {str(e)}"
            )
    
    # Intentar método directo primero (puede fallar por cambios en YouTube Music)
    try:
        result = await service.get_mood_playlists(params)
        
        if not result:
            # Si resultado vacío, intentar búsqueda alternativa
            if not genre_name:
                genre_name = await service.get_genre_name_from_params(params)
            
            if genre_name:
                results = await service.get_mood_playlists_alternative(genre_name)
                return {
                    "playlists": results,
                    "method": "alternative_search",
                    "genre_name": genre_name,
                    "message": "Método directo devolvió resultado vacío, se usó búsqueda alternativa"
                }
            
            return {
                "playlists": [],
                "message": "No se encontraron playlists para este género/mood.",
                "params": params
            }
        
        return {
            "playlists": result,
            "method": "direct"
        }
    except Exception as e:
        error_msg = str(e)
        
        # Si hay error de parsing, usar búsqueda alternativa automáticamente
        if 'musicTwoRowItemRenderer' in error_msg or 'renderer' in error_msg.lower() or 'parsear' in error_msg.lower():
            # Obtener nombre del género
            if not genre_name:
                genre_name = await service.get_genre_name_from_params(params)
            
            if genre_name:
                try:
                    results = await service.get_mood_playlists_alternative(genre_name)
                    return {
                        "playlists": results,
                        "method": "alternative_search",
                        "genre_name": genre_name,
                        "message": "Se usó búsqueda alternativa debido a error en get_mood_playlists()",
                        "params": params
                    }
                except Exception as alt_error:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "error": "Error en búsqueda alternativa",
                            "original_error": str(e),
                            "alternative_error": str(alt_error),
                            "params": params,
                            "genre_name": genre_name,
                            "suggestion": f"Intenta: /api/v1/search/?q={genre_name}&filter=playlists"
                        }
                    )
            
            # Si no se pudo obtener nombre, sugerir usar búsqueda directa
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Error al parsear respuesta de YouTube Music",
                    "message": "get_mood_playlists() falló y no se pudo obtener el nombre del género automáticamente.",
                    "params": params,
                    "solutions": [
                        f"Usa búsqueda directa: /api/v1/explore/moods/{params}?use_search=true&genre_name=Cumbia",
                        f"O directamente: /api/v1/search/?q=Cumbia&filter=playlists",
                        "Actualiza ytmusicapi: pip install --upgrade ytmusicapi"
                    ]
                }
            )
        
        # Otros errores
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/charts",
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
        True, 
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
        
        # Ensure we have top_songs and trending
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
        
        return {
            "top_songs": top_songs_data,
            "trending": trending_data,
            "country": country or "global"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/category/{category_params}",
    summary="Get category playlists (alias)",
    description="Alias para `/explore/moods/{params}`. Obtiene playlists de una categoría.",
    response_description="Lista de playlists de la categoría",
    responses={
        200: {"description": "Playlists obtenidas exitosamente"},
        500: {"description": "Error al cargar categoría"}
    }
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando categoría: {str(e)}")
