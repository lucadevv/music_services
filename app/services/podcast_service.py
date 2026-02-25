"""Service for podcasts."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
import json
from app.core.cache import cache_result


class PodcastService:
    """Service for podcast management."""
    
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
    
    @cache_result(ttl=86400)
    async def get_channel(self, channel_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get channel information."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_channel, channel_id, limit)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canal {channel_id}")
    
    @cache_result(ttl=3600)
    async def get_channel_episodes(
        self, 
        channel_id: str, 
        limit: int = 25,
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get channel episodes."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_channel_episodes, channel_id, limit, params)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener episodios del canal {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_podcast(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get podcast information."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_podcast, browse_id, limit)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener podcast {browse_id}")
    
    @cache_result(ttl=86400)
    async def get_episode(self, browse_id: str) -> Dict[str, Any]:
        """Get episode information."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_episode, browse_id)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener episodio {browse_id}")
    
    @cache_result(ttl=3600)
    async def get_episodes_playlist(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get episodes playlist."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_episodes_playlist, browse_id, limit)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist de episodios {browse_id}")
