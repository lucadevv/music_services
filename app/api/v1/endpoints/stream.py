"""Stream endpoints."""
import logging

from fastapi import APIRouter, Depends, Path, Query, HTTPException, Header, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import httpx
import asyncio
from app.services.stream_service import StreamService
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
from app.schemas.stream import StreamUrlResponse, StreamBatchResponse
from app.schemas.stream_management import (
    CacheStatsResponse,
    CacheClearResponse,
    CacheInfoResponse,
    CacheDeleteResponse,
    StreamCacheStatusResponse,
)

router = APIRouter(tags=["stream"])
logger = logging.getLogger(__name__)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


# ============================================
# PROXY STREAM ENDPOINT - Reproduce audio directamente
# ============================================

@router.get(
    "/proxy/{video_id}",
    summary="Proxy de streaming de audio",
    description="Endpoint de streaming de audio que evita problemas de CORS. El backend hace proxy del audio de YouTube.",
    responses={
        200: {
            "description": "Stream de audio",
            "content": {
                "audio/mpeg": {},
                "audio/mp4": {},
                "audio/*": {}
            }
        },
        404: {"description": "Audio no encontrado"},
        500: {"description": "Error al obtener stream"}
    }
)
async def proxy_stream_audio(
    video_id: str = Path(..., description="ID del video de YouTube"),
    service: StreamService = Depends(get_stream_service)
):
    """
    Endpoint de proxy de streaming.
    
    Este endpoint:
    1. Obtiene la URL de stream de yt-dlp (usa cache)
    2.Hace streaming del audio directamente al cliente
    3. Evita problemas de CORS y URLs incompatibles
    
    Ejemplo de uso en Flutter:
    ```dart
    // Usar este endpoint en lugar de la URL directa de YouTube
    final streamUrl = 'http://backend:8000/api/v1/stream/proxy/$videoId';
    await player.setUrl(streamUrl);
    ```
    """
    validate_video_id(video_id)
    
    try:
        # 1. Obtener la URL de streaming (usa cache automáticamente)
        stream_data = await service.get_stream_url(video_id, bypass_cache=False)
        audio_url = stream_data.get("streamUrl") or stream_data.get("stream_url")
        
        if not audio_url:
            raise HTTPException(status_code=404, detail="No se pudo obtener la URL de audio")
        
        # 2. Configurar el streaming con headers apropiados
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
            "Accept": "*/*",
            "Referer": "https://www.youtube.com/",
        }
        
        # 3. Crear el cliente HTTP para streaming
        async def stream_generator():
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                async with client.stream("GET", audio_url, headers=headers, follow_redirects=True) as response:
                    # 403 = stream URL expired → clear cache and retry with fresh URL
                    if response.status_code == 403:
                        logger.info(f"🔄 Stream URL expired for {video_id}, fetching fresh...")
                        fresh_data = await service.get_stream_url(video_id, bypass_cache=True)
                        fresh_url = fresh_data.get("streamUrl")
                        if not fresh_url:
                            raise HTTPException(status_code=502, detail="No se pudo obtener URL fresca de audio")
                        # Retry with fresh URL
                        async with client.stream("GET", fresh_url, headers=headers, follow_redirects=True) as retry_response:
                            if retry_response.status_code != 200:
                                raise HTTPException(status_code=502, detail=f"Error del servidor de audio: {retry_response.status_code}")
                            content_type = retry_response.headers.get("content-type", "audio/mpeg")
                            async for chunk in retry_response.aiter_bytes(chunk_size=8192):
                                yield chunk
                        return
                    
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Error del servidor de audio: {response.status_code}"
                        )
                    
                    # Determinar content-type
                    content_type = response.headers.get("content-type", "audio/mpeg")
                    
                    # Streaming del contenido
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
        
        # 4. Devolver como streaming response
        return StreamingResponse(
            stream_generator(),
            media_type="audio/mpeg",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=14400",  # 4 horas como las URLs de YouTube
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reproducir audio: {str(e)}")


# ============================================
# BATCH ENDPOINT - Optimizado con MGET como playlists
# ============================================

@router.get(
    "/batch",
    summary="Get multiple stream URLs",
    description="Obtiene URLs de stream para múltiples videos. Usa MGET de Redis para optimizar cache como playlists.",
    response_description="Lista de URLs de stream con metadatos",
    response_model=StreamBatchResponse,
    responses={
        200: {
            "description": "Stream URLs obtenidas exitosamente",
        },
        400: {"description": "Lista vacía o muy larga"},
        **COMMON_ERROR_RESPONSES
    }
)
async def get_batch_stream_urls(
    video_ids: str = Query(..., alias="ids", description="Lista de IDs separada por comas (máximo 50)"),
    bypass_cache: bool = Query(False, description="Si true, ignora cache y obtiene URLs frescas de YouTube"),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """Returns a dict with results and summary - using Dict[str, Any] for flexibility."""
    video_id_list = [vid.strip() for vid in video_ids.split(',') if vid.strip()]
    
    if not video_id_list:
        raise HTTPException(status_code=400, detail="Lista de videos vacía")
    
    if len(video_id_list) > 50:
        raise HTTPException(status_code=400, detail="Máximo 50 videos por request")
    
    items = [{"videoId": vid} for vid in video_id_list]
    
    enriched_items = await service.enrich_items_with_streams(
        items, 
        include_stream_urls=True,
        bypass_cache=bypass_cache
    )
    
    results = []
    cached_count = 0
    fetched_count = 0
    
    for item in enriched_items:
        video_id = item.get("videoId")
        stream_url = item.get("stream_url")
        cached = stream_url is not None
        
        if cached:
            cached_count += 1
        else:
            fetched_count += 1
        
        results.append({
            "videoId": video_id,
            "url": stream_url,
            "title": item.get("title"),
            "artist": item.get("artist"),
            "duration": item.get("duration"),
            "thumbnail": item.get("thumbnail"),
            "cached": cached,
            "error": None if stream_url else "No se pudo obtener URL"
        })
    
    return {
        "results": results,
        "summary": {
            "total": len(results),
            "cached": cached_count,
            "fetched": fetched_count,
            "failed": len(results) - cached_count - fetched_count
        }
    }


# ============================================
# CACHE MANAGEMENT ENDPOINTS - BEFORE /{video_id}
# ============================================

@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    summary="Get cache statistics",
    description="Muestra estadísticas del cache de Redis.",
)
async def get_stream_cache_stats() -> CacheStatsResponse:
    """Muestra estadísticas del cache."""
    stats = await get_cache_stats()
    return CacheStatsResponse(**stats)


@router.delete(
    "/cache",
    response_model=CacheClearResponse,
    summary="Clear all stream cache",
    description="Limpia todo el cache de streams.",
)
async def clear_all_stream_cache() -> CacheClearResponse:
    """Limpia todo el cache de streams."""
    await clear_cache("music:stream")
    return CacheClearResponse(status="cleared", pattern="music:stream")


@router.get(
    "/cache/info/{video_id}",
    response_model=CacheInfoResponse,
    summary="Check cached stream URL for a video",
    description="Verifica si hay una URL de stream cached para un video y muestra info.",
)
async def get_stream_cache_info(
    video_id: str = Path(..., description="ID del video"),
) -> CacheInfoResponse:
    """Muestra información del cache para un video."""
    validate_video_id(video_id)
    
    metadata_key = f"music:stream:metadata:{video_id}"
    stream_url_key = f"music:stream:url:{video_id}"
    
    metadata_exists = await has_cached_key(metadata_key)
    url_exists = await has_cached_key(stream_url_key)
    
    metadata_timestamp = await get_cached_timestamp(metadata_key) if metadata_exists else 0
    url_timestamp = await get_cached_timestamp(stream_url_key) if url_exists else 0
    
    metadata_cached = await get_cached_value(metadata_key) if metadata_exists else None
    url_cached = await get_cached_value(stream_url_key) if url_exists else None
    
    return CacheInfoResponse(
        videoId=video_id,
        cached={
            "metadata": metadata_exists,
            "metadata_timestamp": metadata_timestamp,
            "metadata_value": metadata_cached,
            "stream_url": url_exists,
            "url_timestamp": url_timestamp,
            "url_value": url_cached[:200] + "..." if url_cached and len(url_cached) > 200 else url_cached
        }
    )


@router.delete(
    "/cache/{video_id}",
    response_model=CacheDeleteResponse,
    summary="Delete cached stream URL for a video",
    description="Elimina la URL de stream cached para un video específico.",
)
async def delete_stream_cache(
    video_id: str = Path(..., description="ID del video"),
) -> CacheDeleteResponse:
    """Elimina el cache de un video específico."""
    validate_video_id(video_id)
    
    # Keys used by StreamService
    metadata_key = f"music:stream:metadata:{video_id}"
    stream_url_key = f"music:stream:url:{video_id}"
    
    deleted_metadata = await delete_cached_key(metadata_key)
    deleted_url = await delete_cached_key(stream_url_key)
    
    return CacheDeleteResponse(
        videoId=video_id,
        deleted={
            "metadata": deleted_metadata,
            "stream_url": deleted_url
        }
    )


# ============================================
# CACHE STATUS ENDPOINT
# ============================================

@router.get(
    "/status/{video_id}",
    response_model=StreamCacheStatusResponse,
    summary="Check if stream URL is cached",
    description="Verifica si la URL de stream está en cache sin hacer llamada a YouTube.",
    response_description="Estado del cache"
)
async def get_stream_cache_status(
    video_id: str = Path(..., description="ID del video"),
    service: StreamService = Depends(get_stream_service)
) -> StreamCacheStatusResponse:
    """
    Verifica el estado del cache para un video.
    """
    validate_video_id(video_id)
    
    is_cached = await service.is_cached(video_id)
    ttl_remaining = await service.get_cache_ttl(video_id) if is_cached else 0
    
    return StreamCacheStatusResponse(
        videoId=video_id,
        cached=is_cached,
        expiresIn=ttl_remaining
    )


# ============================================
# SINGLE VIDEO ENDPOINT - MUST BE LAST
# ============================================

@router.get(
    "/{video_id}",
    response_model=StreamUrlResponse,
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
) -> StreamUrlResponse:
    """
    Obtiene la URL directa de stream de audio de una canción.
    """
    validate_video_id(video_id)
    result = await service.get_stream_url(video_id, bypass_cache=bypass_cache)
    return StreamUrlResponse(**result)
