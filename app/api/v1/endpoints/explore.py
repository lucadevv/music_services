"""Explore endpoints - Public content: charts, moods, genres."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional
from ytmusicapi import YTMusic
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.ytmusic_client import get_ytmusic
from app.services.explore_service import ExploreService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


def get_explore_service(ytmusic: YTMusic = Depends(get_ytmusic)) -> ExploreService:
    """Dependency to get explore service."""
    return ExploreService(ytmusic)


@router.get("/")
async def explore_music(
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails for charts"),
    service: ExploreService = Depends(get_explore_service)
):
    """
    Get explore content (moods, genres, charts).
    
    Returns:
    - moods_genres: Lista de categorías de moods/géneros (cada una tiene 'params' para obtener playlists)
    - home: Contenido de la página principal
    - charts: Top songs y trending (con stream_url y thumbnail si include_stream_urls=true)
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


@router.get("/moods")
async def get_mood_categories(service: ExploreService = Depends(get_explore_service)):
    """
    Get mood categories.
    
    Returns dict with sections: 'For you', 'Genres', 'Moods & moments'.
    Each category has a 'params' field and 'title'.
    Use that 'params' value in /explore/moods/{params} to get playlists for that category.
    
    Example structure:
    {
        'For you': [{'params': '...', 'title': '1980s'}, ...],
        'Genres': [{'params': '...', 'title': 'Dance & Electronic'}, ...],
        'Moods & moments': [{'params': '...', 'title': 'Chill'}, ...]
    }
    """
    try:
        categories = await service.get_mood_categories()
        return {
            "categories": categories,
            "structure": "Las categorías están organizadas en secciones: 'For you', 'Genres', 'Moods & moments'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/moods/{params}")
async def get_mood_playlists(
    params: str,
    genre_name: Optional[str] = Query(None, description="Nombre del género (recomendado si get_mood_playlists falla)"),
    use_search: bool = Query(False, description="Forzar uso de búsqueda en lugar de get_mood_playlists"),
    service: ExploreService = Depends(get_explore_service)
):
    """
    Get mood/genre playlists by params.
    
    Use the 'params' value from a mood/genre category to get playlists.
    Each playlist has a 'playlistId' that can be used in /api/v1/playlists/{playlistId}
    
    Nota: Si get_mood_playlists() falla (error de parseo), se usará automáticamente
    búsqueda alternativa. Puedes forzar búsqueda con ?use_search=true
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


@router.get("/charts")
async def get_charts(
    country: Optional[str] = Query(None, description="Country code (e.g., 'US', 'PE')"),
    include_stream_urls: bool = Query(True, description="Include stream URLs and best thumbnails"),
    service: ExploreService = Depends(get_explore_service)
):
    """
    Get charts (top songs and trending).
    
    Returns top songs and trending music with:
    - stream_url: Direct audio stream URL (best quality)
    - thumbnail: Best quality thumbnail URL
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


@router.get("/category/{category_params}")
async def get_category(
    category_params: str,
    service: ExploreService = Depends(get_explore_service)
):
    """
    Get category content by params (alias for mood playlists).
    
    This is the same as /explore/moods/{params} - use the params from a mood/genre category.
    """
    try:
        result = await service.get_mood_playlists(category_params)
        return {
            "playlists": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando categoría: {str(e)}")
