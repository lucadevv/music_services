"""Service for streaming audio."""
import json
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
import yt_dlp
from app.core.config import get_settings


class StreamService:
    """Service for audio streaming."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def get_stream_url(self, video_id: str) -> Dict[str, Any]:
        """Get audio stream URL using yt-dlp."""
        try:
            url = f"https://music.youtube.com/watch?v={video_id}"
            
            browser_path = Path(self.settings.BROWSER_JSON_PATH)
            if not browser_path.exists():
                return {"detail": f"No se encontró el archivo {self.settings.BROWSER_JSON_PATH}"}
            
            with open(browser_path, 'r') as f:
                headers = json.load(f)
            
            # Separar cookie para evitar warnings
            cookie = headers.pop('cookie', None)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio/best',
                'http_headers': headers
            }
            if cookie:
                ydl_opts['cookie'] = cookie
            
            # Ejecutar yt-dlp en thread para no bloquear
            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await asyncio.to_thread(extract_info)
            audio_url = None
            
            # Buscar formato de audio puro
            for f in info.get('adaptive_formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_url = f['url']
                    break
            
            # Fallback a formatos con audio
            if not audio_url:
                for f in info.get('formats', []):
                    if f.get('acodec') != 'none':
                        audio_url = f['url']
                        break
            
            if audio_url:
                return {
                    "title": info.get('title'),
                    "artist": info.get('artist', info.get('uploader')),
                    "duration": info.get('duration'),
                    "thumbnail": info.get('thumbnail'),
                    "url": audio_url
                }
            
            return {"detail": "yt-dlp no pudo obtener el stream. Verifica el ID o tus cookies."}
        
        except Exception as e:
            raise Exception(f"Error obteniendo stream: {str(e)}")
