"""Service for browsing YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class BrowseService:
    """Service for browsing music content."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    @cache_result(ttl=86400)
    async def get_home(self) -> List[Dict[str, Any]]:
        """Get home page content."""
        return await asyncio.to_thread(self.ytmusic.get_home)
    
    @cache_result(ttl=86400)
    async def get_artist(self, channel_id: str) -> Dict[str, Any]:
        """Get artist information."""
        return await asyncio.to_thread(self.ytmusic.get_artist, channel_id)
    
    @cache_result(ttl=86400)
    async def get_artist_albums(
        self, 
        channel_id: str, 
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get artist albums."""
        return await asyncio.to_thread(self.ytmusic.get_artist_albums, channel_id, params)
    
    @cache_result(ttl=86400)
    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album information."""
        return await asyncio.to_thread(self.ytmusic.get_album, album_id)
    
    @cache_result(ttl=86400)
    async def get_album_browse_id(self, album_id: str) -> Optional[str]:
        """Get album browse ID."""
        return await asyncio.to_thread(self.ytmusic.get_album_browse_id, album_id)
    
    @cache_result(ttl=86400)
    async def get_song(self, video_id: str, signature_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """Get song metadata."""
        return await asyncio.to_thread(self.ytmusic.get_song, video_id, signature_timestamp)
    
    @cache_result(ttl=3600)
    async def get_song_related(self, video_id: str) -> List[Dict[str, Any]]:
        """Get related songs."""
        return await asyncio.to_thread(self.ytmusic.get_song_related, video_id)
    
    @cache_result(ttl=86400)
    async def get_lyrics(self, browse_id: str) -> Dict[str, Any]:
        """Get song lyrics."""
        return await asyncio.to_thread(self.ytmusic.get_lyrics, browse_id)
