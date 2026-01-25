"""Service for playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class PlaylistService:
    """Service for reading public playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
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
        return await asyncio.to_thread(
            self.ytmusic.get_playlist,
            normalized_id, 
            limit, 
            related, 
            suggestions_limit
        )
