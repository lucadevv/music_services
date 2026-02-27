"""Service for podcasts."""
from typing import Optional, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.core.cache import cache_result


class PodcastService(BaseService):
    """Service for podcast management."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the podcast service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    @cache_result(ttl=86400)
    async def get_channel(self, channel_id: str, limit: int = 25) -> Dict[str, Any]:
        """
        Get channel information.
        
        Args:
            channel_id: Channel ID.
            limit: Maximum number of results.
        
        Returns:
            Channel information dictionary.
        """
        self._log_operation("get_channel", channel_id=channel_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_channel, channel_id, limit)
            self.logger.info(f"Retrieved channel: {channel_id}")
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
        """
        Get channel episodes.
        
        Args:
            channel_id: Channel ID.
            limit: Maximum number of episodes.
            params: Pagination parameters.
        
        Returns:
            Episodes dictionary.
        """
        self._log_operation("get_channel_episodes", channel_id=channel_id)
        
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_channel_episodes, 
                channel_id, 
                limit, 
                params
            )
            self.logger.info(f"Retrieved episodes for channel: {channel_id}")
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener episodios del canal {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_podcast(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """
        Get podcast information.
        
        Args:
            browse_id: Podcast browse ID.
            limit: Maximum number of episodes.
        
        Returns:
            Podcast information dictionary.
        """
        self._log_operation("get_podcast", browse_id=browse_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_podcast, browse_id, limit)
            self.logger.info(f"Retrieved podcast: {browse_id}")
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener podcast {browse_id}")
    
    @cache_result(ttl=86400)
    async def get_episode(self, browse_id: str) -> Dict[str, Any]:
        """
        Get episode information.
        
        Args:
            browse_id: Episode browse ID.
        
        Returns:
            Episode information dictionary.
        """
        self._log_operation("get_episode", browse_id=browse_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_episode, browse_id)
            self.logger.info(f"Retrieved episode: {browse_id}")
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener episodio {browse_id}")
    
    @cache_result(ttl=3600)
    async def get_episodes_playlist(self, browse_id: str, limit: int = 25) -> Dict[str, Any]:
        """
        Get episodes playlist.
        
        Args:
            browse_id: Podcast browse ID.
            limit: Maximum number of episodes.
        
        Returns:
            Episodes playlist dictionary.
        """
        self._log_operation("get_episodes_playlist", browse_id=browse_id)
        
        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_episodes_playlist, 
                browse_id, 
                limit
            )
            self.logger.info(f"Retrieved episodes playlist for: {browse_id}")
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist de episodios {browse_id}")
