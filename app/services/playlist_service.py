"""Service for playlists."""
from typing import Optional, Dict, Any, List
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
    
    @cache_result(ttl=86400)  # 24 horas - playlists no cambian frecuentemente
    async def get_playlist(
        self, 
        playlist_id: str, 
        limit: int = 100,
        related: bool = False,
        suggestions_limit: int = 0,
        start_index: int = 0
    ) -> Dict[str, Any]:
        """
        Get playlist information with pagination support.
        
        Args:
            playlist_id: Playlist ID.
            limit: Maximum number of tracks to return.
            related: Include related songs.
            suggestions_limit: Limit for suggestions.
            start_index: Starting index for pagination (0-based).
        
        Returns:
            Playlist information dictionary with pagination info.
        """
        normalized_id = self._normalize_playlist_id(playlist_id)
        self._log_operation("get_playlist", playlist_id=normalized_id, limit=limit, start_index=start_index)
        
        try:
            # ytmusicapi supports limit parameter
            result = await asyncio.to_thread(
                self.ytmusic.get_playlist,
                normalized_id, 
                limit=limit,  # Max tracks to retrieve
                related=related, 
                suggestions_limit=suggestions_limit
            )
            if result is None:
                raise ResourceNotFoundError(
                    message="Playlist no encontrada.",
                    details={"resource_type": "playlist", "playlist_id": playlist_id}
                )
            
            # Apply start_index slicing if needed
            tracks = result.get('tracks', [])
            if start_index > 0 and start_index < len(tracks):
                tracks = tracks[start_index:]
                result['tracks'] = tracks
                result['start_index'] = start_index
            
            # Add pagination metadata
            result['pagination'] = {
                'start_index': start_index,
                'limit': limit,
                'total_tracks': len(result.get('tracks', []))
            }
            
            track_count = len(result.get('tracks', []))
            self.logger.info(f"Retrieved playlist {playlist_id}: {track_count} tracks (start={start_index}, limit={limit})")
            return result
        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist {playlist_id}")
