"""Service for podcasts."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class PodcastService:
    """Service for podcast management."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    @cache_result(ttl=86400)
    async def get_channel(self, channel_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get channel information."""
        return await asyncio.to_thread(self.ytmusic.get_channel, channel_id, limit)
    
    @cache_result(ttl=3600)
    async def get_channel_episodes(
        self, 
        channel_id: str, 
        limit: int = 25,
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get channel episodes."""
        return await asyncio.to_thread(self.ytmusic.get_channel_episodes, channel_id, limit, params)
    
    @cache_result(ttl=86400)
    async def get_podcast(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get podcast information."""
        return await asyncio.to_thread(self.ytmusic.get_podcast, browse_id, limit)
    
    @cache_result(ttl=86400)
    async def get_episode(self, browse_id: str) -> Dict[str, Any]:
        """Get episode information."""
        return await asyncio.to_thread(self.ytmusic.get_episode, browse_id)
    
    @cache_result(ttl=3600)
    async def get_episodes_playlist(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """Get episodes playlist."""
        return await asyncio.to_thread(self.ytmusic.get_episodes_playlist, browse_id, limit)
