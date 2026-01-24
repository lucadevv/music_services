"""Service for playlists - Solo lectura de playlists públicas."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class PlaylistService:
    """Service for reading public playlists (no gestión personal)."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    def _normalize_playlist_id(self, playlist_id: str) -> str:
        """Normalize playlist ID - remove VL prefix if present."""
        # Los browseId de búsqueda vienen con prefijo VL, pero get_playlist() necesita sin prefijo
        if playlist_id.startswith('VL'):
            return playlist_id[2:]  # Remover 'VL'
        return playlist_id
    
    @cache_result(ttl=600)  # Cache for 10 minutes (playlists can change)
    async def get_playlist(
        self, 
        playlist_id: str, 
        limit: int = 100,
        related: bool = False,
        suggestions_limit: int = 0
    ) -> Dict[str, Any]:
        """
        Get playlist information (solo lectura).
        
        Acepta tanto playlistId como browseId (normaliza automáticamente).
        Obtiene las canciones de una playlist pública.
        Cada canción tiene un 'videoId' para obtener el stream.
        """
        # Normalizar el ID (remover prefijo VL si existe)
        normalized_id = self._normalize_playlist_id(playlist_id)
        
        return await asyncio.to_thread(
            self.ytmusic.get_playlist,
            normalized_id, 
            limit, 
            related, 
            suggestions_limit
        )
