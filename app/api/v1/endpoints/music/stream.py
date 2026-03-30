"""Stream endpoints for music playback."""
import logging
from fastapi import APIRouter, Depends, Path, Query, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import httpx

from app.services.stream_service import StreamService
from app.core.validators import validate_video_id
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.schemas.stream import StreamUrlResponse, StreamBatchResponse
from app.core.auth_docs import require_music_bearer_header

router = APIRouter()
logger = logging.getLogger(__name__)


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


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
    _auth: None = Depends(require_music_bearer_header),
    service: StreamService = Depends(get_stream_service)
):
    """
    Endpoint de proxy de streaming.
    
    Este endpoint:
    1. Obtiene la URL de stream de yt-dlp (usa cache)
    2. Hace streaming del audio directamente al cliente
    3. Evita problemas de CORS y URLs incompatibles
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
                        fresh_url = fresh_data.get("streamUrl") or fresh_data.get("stream_url")
                        if not fresh_url:
                            raise HTTPException(status_code=502, detail="No se pudo obtener URL fresca de audio")
                        # Retry with fresh URL
                        async with client.stream("GET", fresh_url, headers=headers, follow_redirects=True) as retry_response:
                            if retry_response.status_code != 200:
                                raise HTTPException(status_code=502, detail=f"Error del servidor de audio: {retry_response.status_code}")
                            async for chunk in retry_response.aiter_bytes(chunk_size=8192):
                                yield chunk
                        return
                    
                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Error del servidor de audio: {response.status_code}"
                        )
                    
                    # Streaming del contenido
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        yield chunk
        
        # 4. Devolver como streaming response
        return StreamingResponse(
            stream_generator(),
            media_type="audio/mpeg",
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=14400",  # 4 horas
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reproducir audio: {str(e)}")


@router.get(
    "/batch",
    summary="Get multiple stream URLs",
    description="Obtiene URLs de stream para múltiples videos. Usa MGET de Redis para optimizar cache.",
    response_description="Lista de URLs de stream con metadatos",
    response_model=StreamBatchResponse,
    responses={200: {"description": "Stream URLs obtenidas exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_batch_stream_urls(
    video_ids: str = Query(..., alias="ids", description="Lista de IDs separada por comas (máximo 50)"),
    bypass_cache: bool = Query(False, description="Si true, ignora cache y obtiene URLs frescas"),
    _auth: None = Depends(require_music_bearer_header),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """Obtiene URLs de stream para múltiples videos."""
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


@router.get(
    "/{video_id}",
    response_model=StreamUrlResponse,
    summary="Get audio stream URL",
    description="Obtiene la URL directa de stream de audio de una canción usando yt-dlp.",
    response_description="URL de stream y metadatos",
    responses={200: {"description": "Stream URL obtenida exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_stream_url(
    video_id: str = Path(..., description="ID del video/canción"),
    bypass_cache: bool = Query(False, description="Si true, ignora la caché"),
    _auth: None = Depends(require_music_bearer_header),
    service: StreamService = Depends(get_stream_service)
) -> StreamUrlResponse:
    """Obtiene la URL directa de stream de audio de una canción."""
    validate_video_id(video_id)
    result = await service.get_stream_url(video_id, bypass_cache=bypass_cache)
    return StreamUrlResponse(**result)
