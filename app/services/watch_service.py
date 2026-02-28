"""Service for watch playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.core.cache import cache_result


class WatchService(BaseService):
    """Service for watch playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the watch service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    @cache_result(ttl=600)
    async def get_watch_playlist(
        self,
        video_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
        limit: int = 25,
        radio: bool = False,
        shuffle: bool = False
    ) -> Dict[str, Any]:
        """
        Get watch playlist (next songs when playing).
        
        Args:
            video_id: Video ID to start from.
            playlist_id: Playlist ID.
            limit: Maximum number of tracks.
            radio: Generate radio playlist.
            shuffle: Shuffle the playlist.
        
        Returns:
            Watch playlist dictionary.
        """
        self._log_operation(
            "get_watch_playlist", 
            video_id=video_id, 
            playlist_id=playlist_id,
            radio=radio,
            shuffle=shuffle
        )
        
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_watch_playlist,
                videoId=video_id,
                playlistId=playlist_id,
                limit=limit,
                radio=radio,
                shuffle=shuffle
            )
            
            tracks = result.get('tracks', []) if result else []
            self.logger.info(
                f"Retrieved watch playlist: {len(tracks)} tracks "
                f"(video_id={video_id}, playlist_id={playlist_id})"
            )
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(
                e, 
                f"obtener watch playlist (video_id: {video_id}, playlist_id: {playlist_id})"
            )
