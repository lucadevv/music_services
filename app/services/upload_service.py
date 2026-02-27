"""Service for uploads."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService


class UploadService(BaseService):
    """Service for upload management."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the upload service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    async def get_library_upload_songs(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get uploaded songs.
        
        Args:
            limit: Maximum number of songs.
            order: Sort order.
        
        Returns:
            List of uploaded songs.
        """
        self._log_operation("get_library_upload_songs", limit=limit)
        result = await asyncio.to_thread(self.ytmusic.get_library_upload_songs, limit, order)
        self.logger.info(f"Retrieved {len(result) if result else 0} uploaded songs")
        return result
    
    async def get_library_upload_artists(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get uploaded artists.
        
        Args:
            limit: Maximum number of artists.
            order: Sort order.
        
        Returns:
            List of uploaded artists.
        """
        self._log_operation("get_library_upload_artists", limit=limit)
        result = await asyncio.to_thread(self.ytmusic.get_library_upload_artists, limit, order)
        self.logger.info(f"Retrieved {len(result) if result else 0} uploaded artists")
        return result
    
    async def get_library_upload_albums(
        self, 
        limit: int = 25, 
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get uploaded albums.
        
        Args:
            limit: Maximum number of albums.
            order: Sort order.
        
        Returns:
            List of uploaded albums.
        """
        self._log_operation("get_library_upload_albums", limit=limit)
        result = await asyncio.to_thread(self.ytmusic.get_library_upload_albums, limit, order)
        self.logger.info(f"Retrieved {len(result) if result else 0} uploaded albums")
        return result
    
    async def get_library_upload_artist(
        self, 
        artist_id: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Get uploaded artist details.
        
        Args:
            artist_id: Artist ID.
            limit: Maximum number of results.
        
        Returns:
            Artist details.
        """
        self._log_operation("get_library_upload_artist", artist_id=artist_id)
        result = await asyncio.to_thread(self.ytmusic.get_library_upload_artist, artist_id, limit)
        self.logger.info(f"Retrieved uploaded artist: {artist_id}")
        return result
    
    async def get_library_upload_album(
        self, 
        album_id: str, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """
        Get uploaded album details.
        
        Args:
            album_id: Album ID.
            limit: Maximum number of results.
        
        Returns:
            Album details.
        """
        self._log_operation("get_library_upload_album", album_id=album_id)
        result = await asyncio.to_thread(self.ytmusic.get_library_upload_album, album_id, limit)
        self.logger.info(f"Retrieved uploaded album: {album_id}")
        return result
    
    async def upload_song(
        self, 
        filepath: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload a song.
        
        Args:
            filepath: Path to the file.
            metadata: Optional metadata.
        
        Returns:
            Upload result.
        """
        self._log_operation("upload_song", filepath=filepath)
        result = await asyncio.to_thread(self.ytmusic.upload_song, filepath, metadata)
        self.logger.info(f"Uploaded song: {filepath}")
        return result
    
    async def delete_upload_entity(
        self, 
        entity_id: str
    ) -> bool:
        """
        Delete uploaded entity.
        
        Args:
            entity_id: Entity ID to delete.
        
        Returns:
            True if successful.
        """
        self._log_operation("delete_upload_entity", entity_id=entity_id)
        result = await asyncio.to_thread(self.ytmusic.delete_upload_entity, entity_id)
        self.logger.info(f"Deleted upload entity: {entity_id}")
        return result
