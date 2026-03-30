"""Service for generic yt-dlp extraction."""
import asyncio
import yt_dlp
import logging
from typing import Any, Dict, Optional, List
from app.services.base_service import BaseService
from app.core.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)

class YtdlpService(BaseService):
    """Service for extracting info from any URL using yt-dlp."""
    
    def __init__(self):
        super().__init__()
    
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """
        Extrae información de cualquier URL soportada por yt-dlp.
        """
        # Opciones básicas para extracción rápida
        ydl_opts = {
            'format': 'best', # Intentar obtener lo mejor por defecto
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0', # Forzar IPv4 para evitar timeouts en algunos sitios
        }
        
        try:
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            # Ejecutar en un hilo separado para no bloquear el loop de eventos de FastAPI
            info = await asyncio.to_thread(_extract)
            
            if not info:
                raise ExternalServiceError(
                    message="No se pudo extraer información de la URL proporcionada.",
                    details={"url": url}
                )
                
            return self._process_info(info)
            
        except Exception as e:
            logger.error(f"Error de extracción yt-dlp para URL {url}: {str(e)}")
            raise ExternalServiceError(
                message=f"Error al procesar la URL con yt-dlp: {str(e)}",
                details={"url": url}
            )

    def _process_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la información cruda de yt-dlp a un formato estandarizado.
        """
        formats = []
        raw_formats = info.get('formats', [])
        
        # Estandarizar formatos
        for f in raw_formats:
            formats.append({
                "formatId": f.get('format_id'),
                "ext": f.get('ext'),
                "resolution": f.get('resolution'),
                "fps": f.get('fps'),
                "acodec": f.get('acodec'),
                "vcodec": f.get('vcodec'),
                "url": f.get('url'),
                "filesize": f.get('filesize') or f.get('filesize_approx')
            })
        
        # Encontrar el mejor audio y video
        best_audio_url = None
        best_video_url = info.get('url') # URL por defecto seleccionada por yt-dlp
        
        # Heurística para mejor audio (solo audio)
        audio_only = [f for f in raw_formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
        if audio_only:
            # Ordenar por calidad de audio aproximada (abr) o bitrate
            audio_only.sort(key=lambda x: (x.get('abr') or 0, x.get('filesize') or 0), reverse=True)
            best_audio_url = audio_only[0].get('url')
        
        # Si no hay audio-only, usar la URL principal como fallback
        if not best_audio_url:
            best_audio_url = best_video_url
            
        return {
            "id": info.get('id'),
            "title": info.get('title'),
            "description": info.get('description'),
            "duration": info.get('duration'),
            "uploader": info.get('uploader'),
            "uploaderUrl": info.get('uploader_url'),
            "thumbnail": info.get('thumbnail'),
            "webpageUrl": info.get('webpage_url'),
            "formats": formats,
            "bestAudioUrl": best_audio_url,
            "bestVideoUrl": best_video_url
        }
