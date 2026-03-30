"""Cache management endpoints for administrators."""
import logging
from fastapi import APIRouter, Depends, Path, HTTPException
from typing import Dict, Any

from app.core.validators import validate_video_id
from app.core.cache_redis import (
    delete_cached_key,
    get_cached_value,
    get_cached_timestamp,
    has_cached_key,
    clear_cache,
    get_cache_stats,
)
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.schemas.stream_management import (
    CacheStatsResponse,
    CacheClearResponse,
    CacheInfoResponse,
    CacheDeleteResponse,
    StreamCacheStatusResponse,
)
from app.api.v1.endpoints.admin.auth import verify_admin_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="Muestra estadísticas detalladas del cache de Redis para streams.",
    responses={200: {"description": "Estadísticas obtenidas"}, **COMMON_ERROR_RESPONSES}
)
async def get_stream_cache_stats(
    _verified: None = Depends(verify_admin_key),
) -> CacheStatsResponse:
    """Muestra estadísticas del cache."""
    stats = await get_cache_stats()
    return CacheStatsResponse(**stats)


@router.delete(
    "/clear",
    response_model=CacheClearResponse,
    summary="Clear all stream cache",
    description="Elimina todas las entradas de cache relacionadas con streams de música.",
    responses={200: {"description": "Cache limpiado"}, **COMMON_ERROR_RESPONSES}
)
async def clear_all_stream_cache(
    _verified: None = Depends(verify_admin_key),
) -> CacheClearResponse:
    """Limpia todo el cache de streams."""
    await clear_cache("music:stream")
    return CacheClearResponse(status="cleared", pattern="music:stream")


@router.get(
    "/info/{video_id}",
    response_model=CacheInfoResponse,
    summary="Check cached stream URL for a video",
    description="Verifica si existe información en cache para un video específico.",
    responses={200: {"description": "Información obtenida"}, **COMMON_ERROR_RESPONSES}
)
async def get_stream_cache_info(
    video_id: str = Path(..., description="ID del video"),
    _verified: None = Depends(verify_admin_key),
) -> CacheInfoResponse:
    """Muestra información del cache para un video."""
    from app.core.exceptions import ValidationError
    
    try:
        validate_video_id(video_id)
    except ValidationError:
        return CacheInfoResponse(
            videoId=video_id,
            cached={
                "metadata": False,
                "metadata_timestamp": 0,
                "metadata_value": None,
                "stream_url": False,
                "url_timestamp": 0,
                "url_value": None
            }
        )
    
    metadata_key = f"music:stream:metadata:{video_id}"
    stream_url_key = f"music:stream:url:{video_id}"
    
    try:
        metadata_exists = await has_cached_key(metadata_key)
        url_exists = await has_cached_key(stream_url_key)
        
        metadata_timestamp = await get_cached_timestamp(metadata_key) if metadata_exists else 0
        url_timestamp = await get_cached_timestamp(stream_url_key) if url_exists else 0
        
        metadata_cached = await get_cached_value(metadata_key) if metadata_exists else None
        url_cached = await get_cached_value(stream_url_key) if url_exists else None
        
        # Safe truncate for display
        url_display = None
        if url_cached and isinstance(url_cached, str):
            url_display = url_cached[:200] + "..." if len(url_cached) > 200 else url_cached
            
        return CacheInfoResponse(
            videoId=video_id,
            cached={
                "metadata": metadata_exists,
                "metadata_timestamp": metadata_timestamp,
                "metadata_value": metadata_cached,
                "stream_url": url_exists,
                "url_timestamp": url_timestamp,
                "url_value": url_display
            }
        )
    except Exception as e:
        logger.error(f"Error getting cache info for {video_id}: {e}")
        raise HTTPException(status_code=500, detail="Error al consultar Redis")


@router.delete(
    "/{video_id}",
    response_model=CacheDeleteResponse,
    summary="Delete cached stream URL for a video",
    description="Elimina la URL de stream cached para un video específico.",
    responses={200: {"description": "Cache eliminado"}, **COMMON_ERROR_RESPONSES}
)
async def delete_stream_cache(
    video_id: str = Path(..., description="ID del video"),
    _verified: None = Depends(verify_admin_key),
) -> CacheDeleteResponse:
    """Elimina el cache para un video."""
    metadata_key = f"music:stream:metadata:{video_id}"
    stream_url_key = f"music:stream:url:{video_id}"
    
    deleted_metadata = await delete_cached_key(metadata_key)
    deleted_url = await delete_cached_key(stream_url_key)
    
    return CacheDeleteResponse(
        videoId=video_id,
        deleted={
            "metadata": deleted_metadata > 0,
            "stream_url": deleted_url > 0
        }
    )


@router.get(
    "/status/{video_id}",
    response_model=StreamCacheStatusResponse,
    summary="Get detailed stream status",
    description="Obtiene estado detallado de expiración y caché de un video.",
    responses={200: {"description": "Estado obtenido"}, **COMMON_ERROR_RESPONSES}
)
async def get_stream_status(
    video_id: str = Path(..., description="ID del video"),
    _verified: None = Depends(verify_admin_key),
) -> StreamCacheStatusResponse:
    """Obtiene estado detallado de un stream."""
    from app.services.stream_service import StreamService
    service = StreamService()
    
    # 1. Check cache info
    stream_url_key = f"music:stream:url:{video_id}"
    exists = await has_cached_key(stream_url_key)
    timestamp = await get_cached_timestamp(stream_url_key) if exists else 0
    
    # 2. Check metadata
    metadata_key = f"music:stream:metadata:{video_id}"
    meta_exists = await has_cached_key(metadata_key)
    
    return StreamCacheStatusResponse(
        videoId=video_id,
        is_cached=exists,
        cached_at=timestamp,
        has_metadata=meta_exists,
        ttl_seconds=await service.get_stream_ttl(video_id)
    )
