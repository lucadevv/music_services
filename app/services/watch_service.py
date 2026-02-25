"""Service for watch playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
import json
from app.core.cache import cache_result


class WatchService:
    """Service for watch playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    def _handle_ytmusic_error(self, error: Exception, operation: str) -> Exception:
        """Handle ytmusicapi errors and provide better error messages."""
        error_msg = str(error)
        
        if "Expecting value" in error_msg or "JSON" in error_msg or "line 1 column 1" in error_msg:
            return Exception(
                f"Error de autenticación o respuesta inválida de YouTube Music. "
                f"Verifica que browser.json sea válido y no esté expirado. "
                f"Operación: {operation}. "
                f"Error original: {error_msg}"
            )
        
        if "rate" in error_msg.lower() or "429" in error_msg:
            return Exception(
                f"Rate limit de YouTube Music. Intenta más tarde. "
                f"Operación: {operation}"
            )
        
        return Exception(f"Error en {operation}: {error_msg}")
    
    @cache_result(ttl=600)
    async def get_watch_playlist(
        self,
        video_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
        limit: int = 25,
        radio: bool = False,
        shuffle: bool = False
    ) -> Dict[str, Any]:
        """Get watch playlist (next songs when playing)."""
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_watch_playlist,
                video_id=video_id,
                playlist_id=playlist_id,
                limit=limit,
                radio=radio,
                shuffle=shuffle
            )
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener watch playlist (video_id: {video_id}, playlist_id: {playlist_id})")
