"""Service for playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.core.cache import cache_result
from app.core.exceptions import ResourceNotFoundError, YTMusicServiceException


class PlaylistService(BaseService):
    """Service for reading public playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the playlist service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    def _normalize_playlist_id(self, playlist_id: str) -> str:
        """
        Normalize playlist ID - remove VL prefix if present.
        
        Args:
            playlist_id: Raw playlist ID.
        
        Returns:
            Normalized playlist ID.
        """
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
        """
        Get playlist information.
        
        Args:
            playlist_id: Playlist ID.
            limit: Maximum number of tracks.
            related: Include related songs.
            suggestions_limit: Limit for suggestions.
        
        Returns:
            Playlist information dictionary.
        """
        normalized_id = self._normalize_playlist_id(playlist_id)
        self._log_operation("get_playlist", playlist_id=normalized_id, limit=limit)
        
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_playlist,
                normalized_id, 
                limit, 
                related, 
                suggestions_limit
            )
            if result is None:
                raise ResourceNotFoundError(
                    message="Playlist no encontrada.",
                    details={"resource_type": "playlist", "playlist_id": playlist_id}
                )
            
            track_count = len(result.get('tracks', []))
            self.logger.info(f"Retrieved playlist {playlist_id}: {track_count} tracks")
            return result
        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist {playlist_id}")
