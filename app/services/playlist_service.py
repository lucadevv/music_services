"""Service for playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
import json
from app.core.cache import cache_result


class PlaylistService:
    """Service for reading public playlists."""
    
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
    
    def _normalize_playlist_id(self, playlist_id: str) -> str:
        """Normalize playlist ID - remove VL prefix if present."""
        if playlist_id.startswith('VL'):
            return playlist_id[2:]
        return playlist_id
    
    @cache_result(ttl=3600)
    async def get_playlist(
        self, 
        playlist_id: str, 
        limit: int = 100,
        related: bool = False,
        suggestions_limit: int = 0
    ) -> Dict[str, Any]:
        """Get playlist information."""
        normalized_id = self._normalize_playlist_id(playlist_id)
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_playlist,
                normalized_id, 
                limit, 
                related, 
                suggestions_limit
            )
            if result is None:
                raise Exception(f"Playlist no encontrada: {playlist_id}")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist {playlist_id}")
