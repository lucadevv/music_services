"""yt-dlp generic extraction endpoints."""
from fastapi import APIRouter, Depends, Query, Body
from typing import Dict, Any

from app.services.ytdlp_service import YtdlpService
from app.schemas.ytdlp import YtdlpRequest, YtdlpResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES

router = APIRouter()

def get_ytdlp_service() -> YtdlpService:
    """Dependency to get yt-dlp service."""
    return YtdlpService()

@router.get(
    "/extract",
    response_model=YtdlpResponse,
    summary="Extract info from any URL",
    description="Extrae metadatos y URLs de descarga de prácticamente cualquier red social o sitio de video/audio usando yt-dlp.",
    responses={200: {"description": "Información extraída exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def extract_info_get(
    url: str = Query(..., description="URL del video/audio a procesar"),
    service: YtdlpService = Depends(get_ytdlp_service)
) -> Dict[str, Any]:
    """Extrae información mediante GET."""
    return await service.extract_info(url)

@router.post(
    "/extract",
    response_model=YtdlpResponse,
    summary="Extract info from any URL (POST)",
    description="Extrae metadatos y URLs de descarga mediante un cuerpo JSON.",
    responses={200: {"description": "Información extraída exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def extract_info_post(
    request: YtdlpRequest = Body(...),
    service: YtdlpService = Depends(get_ytdlp_service)
) -> Dict[str, Any]:
    """Extrae información mediante POST."""
    return await service.extract_info(request.url)
