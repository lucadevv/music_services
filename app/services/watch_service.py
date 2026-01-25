"""Service for watch playlists."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class WatchService:
    """Service for watch playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
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
        return await asyncio.to_thread(
            self.ytmusic.get_watch_playlist,
            video_id=video_id,
            playlist_id=playlist_id,
            limit=limit,
            radio=radio,
            shuffle=shuffle
        )
