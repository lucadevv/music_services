"""Stream endpoints."""
from fastapi import APIRouter, Depends, Path, Query, HTTPException
from typing import Dict, Any, List
from app.services.stream_service import StreamService
from app.core.validators import validate_video_id
from app.schemas.errors import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["stream"])


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


# ============================================
# BATCH ENDPOINT - MUST BE BEFORE /{video_id}
# ============================================

@router.get(
    "/batch",
    summary="Get multiple stream URLs",
    description="Obtiene URLs de stream para múltiples videos a la vez. Optimizado para Play All y listas.",
    response_description="Lista de URLs de stream con metadatos",
    responses={
        200: {
            "description": "Stream URLs obtenidas exitosamente",
        },
        400: {"description": "Lista vacía o muy larga"},
        **COMMON_ERROR_RESPONSES
    }
)
async def get_batch_stream_urls(
    video_ids: str = Query(..., alias="ids", description="Lista de IDs separada por comas (máximo 20)"),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene URLs de stream para múltiples videos a la vez.
    
    **Ejemplo:**
    `/stream/batch?ids=dQw4w9WgXcQ,9bZkp7q19f0,kJQP7kiw5Fk`
    """
    # Parse video IDs from comma-separated string
    video_id_list = [vid.strip() for vid in video_ids.split(',') if vid.strip()]
    
    # Validar lista
    if not video_id_list:
        raise HTTPException(status_code=400, detail="Lista de videos vacía")
    
    if len(video_id_list) > 20:
        raise HTTPException(status_code=400, detail="Máximo 20 videos por request")
    
    # Eliminar duplicados
    video_id_list = list(dict.fromkeys(video_id_list))
    
    results = []
    cached_count = 0
    
    # Obtener todas las URLs (usa cache automáticamente)
    for video_id in video_id_list:
        try:
            validate_video_id(video_id)
            stream_data = await service.get_stream_url(video_id, bypass_cache=False)
            from_cache = stream_data.get("from_cache", False)
            
            results.append({
                "videoId": video_id,
                "title": stream_data.get("title"),
                "artist": stream_data.get("artist"),
                "duration": stream_data.get("duration"),
                "thumbnail": stream_data.get("thumbnail"),
                "url": stream_data.get("url"),
                "cached": from_cache
            })
            if from_cache:
                cached_count += 1
            
        except Exception as e:
            results.append({
                "videoId": video_id,
                "error": str(e),
                "url": None,
                "cached": False
            })
    
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "cached": cached_count,
            "failed": len(results) - cached_count
        }
    }


# ============================================
# CACHE STATUS ENDPOINT
# ============================================

@router.get(
    "/status/{video_id}",
    summary="Check if stream URL is cached",
    description="Verifica si la URL de stream está en cache sin hacer llamada a YouTube.",
    response_description="Estado del cache"
)
async def get_stream_cache_status(
    video_id: str = Path(..., description="ID del video"),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Verifica el estado del cache para un video.
    """
    validate_video_id(video_id)
    
    is_cached = await service.is_cached(video_id)
    ttl_remaining = await service.get_cache_ttl(video_id) if is_cached else 0
    
    return {
        "videoId": video_id,
        "cached": is_cached,
        "expiresIn": ttl_remaining
    }


# ============================================
# SINGLE VIDEO ENDPOINT - MUST BE LAST
# ============================================

@router.get(
    "/{video_id}",
    summary="Get audio stream URL",
    description="Obtiene la URL directa de stream de audio de una canción usando yt-dlp. Incluye caché inteligente y circuit breaker.",
    response_description="URL de stream y metadatos",
    responses={
        200: {
            "description": "Stream URL obtenida exitosamente",
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_stream_url(
    video_id: str = Path(..., description="ID del video/canción"),
    bypass_cache: bool = Query(False, description="Si true, ignora la caché y genera una URL fresca"),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene la URL directa de stream de audio de una canción.
    """
    validate_video_id(video_id)
    return await service.get_stream_url(video_id, bypass_cache=bypass_cache)
