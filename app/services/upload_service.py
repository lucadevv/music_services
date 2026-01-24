"""Service for uploads."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio


class UploadService:
    """Service for upload management."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    async def get_library_upload_songs(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get uploaded songs."""
        return await asyncio.to_thread(self.ytmusic.get_library_upload_songs, limit, order)
    
    async def get_library_upload_artists(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get uploaded artists."""
        return await asyncio.to_thread(self.ytmusic.get_library_upload_artists, limit, order)
    
    async def get_library_upload_albums(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get uploaded albums."""
        return await asyncio.to_thread(self.ytmusic.get_library_upload_albums, limit, order)
    
    async def get_library_upload_artist(
        self, 
        artist_id: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get uploaded artist details."""
        return await asyncio.to_thread(self.ytmusic.get_library_upload_artist, artist_id, limit)
    
    async def get_library_upload_album(
        self, 
        album_id: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Get uploaded album details."""
        return await asyncio.to_thread(self.ytmusic.get_library_upload_album, album_id, limit)
    
    async def upload_song(
        self, 
        filepath: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a song."""
        return await asyncio.to_thread(self.ytmusic.upload_song, filepath, metadata)
    
    async def delete_upload_entity(
        self, 
        entity_id: str
    ) -> bool:
        """Delete uploaded entity."""
        return await asyncio.to_thread(self.ytmusic.delete_upload_entity, entity_id)
