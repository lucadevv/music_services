"""Service for browsing YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.core.cache import cache_result
from app.core.exceptions import ResourceNotFoundError, YTMusicServiceException


class BrowseService(BaseService):
    """Service for browsing music content."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the browse service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    @cache_result(ttl=86400)
    async def get_home(self) -> List[Dict[str, Any]]:
        """
        Get home page content.
        
        Returns:
            List of home page sections.
        """
        self._log_operation("get_home")
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_home)
            content = result if result is not None else []
            self.logger.info(f"Retrieved home page: {len(content)} sections")
            return content
        except Exception as e:
            raise self._handle_ytmusic_error(e, "obtener home")
    
    @cache_result(ttl=86400)
    async def get_artist(self, channel_id: str) -> Dict[str, Any]:
        """
        Get artist information.
        
        Args:
            channel_id: Artist channel ID.
        
        Returns:
            Artist information dictionary.
        """
        self._log_operation("get_artist", channel_id=channel_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_artist, channel_id)
            if result is None:
                raise ResourceNotFoundError(
                    message="Artista no encontrado.",
                    details={"resource_type": "artist", "channel_id": channel_id}
                )
            self.logger.info(f"Retrieved artist: {channel_id}")
            return result
        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener artista {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_artist_albums(
        self, 
        channel_id: str, 
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get artist albums.
        
        Args:
            channel_id: Artist channel ID.
            params: Pagination parameters.
        
        Returns:
            Artist albums dictionary.
        """
        self._log_operation("get_artist_albums", channel_id=channel_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_artist_albums, channel_id, params)
            albums = result if result is not None else {}
            self.logger.info(f"Retrieved albums for artist: {channel_id}")
            return albums
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbumes de artista {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """
        Get album information.
        
        Args:
            album_id: Album ID.
        
        Returns:
            Album information dictionary.
        """
        self._log_operation("get_album", album_id=album_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_album, album_id)
            if result is None:
                raise ResourceNotFoundError(
                    message="Álbum no encontrado.",
                    details={"resource_type": "album", "album_id": album_id}
                )
            self.logger.info(f"Retrieved album: {album_id}")
            return result
        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbum {album_id}")
    
    @cache_result(ttl=86400)
    async def get_album_browse_id(self, album_id: str) -> Optional[str]:
        """
        Get album browse ID.
        
        Args:
            album_id: Album ID.
        
        Returns:
            Browse ID string or None.
        """
        self._log_operation("get_album_browse_id", album_id=album_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_album_browse_id, album_id)
            self.logger.debug(f"Retrieved browse ID for album {album_id}: {result}")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener browse ID de álbum {album_id}")
    
    @cache_result(ttl=86400)
    async def get_song(self, video_id: str, signature_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Get song metadata.
        
        Args:
            video_id: Video ID.
            signature_timestamp: Optional signature timestamp.
        
        Returns:
            Song metadata dictionary.
        """
        self._log_operation("get_song", video_id=video_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_song, video_id, signature_timestamp)
            if result is None:
                raise ResourceNotFoundError(
                    message="Canción no encontrada.",
                    details={"resource_type": "song", "video_id": video_id}
                )
            self.logger.info(f"Retrieved song: {video_id}")
            return result
        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canción {video_id}")
    
    @cache_result(ttl=3600)
    async def get_song_related(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get related songs.
        
        Args:
            video_id: Video ID.
        
        Returns:
            List of related songs.
        """
        self._log_operation("get_song_related", video_id=video_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_song_related, video_id)
            related = result if result is not None else []
            self.logger.info(f"Retrieved {len(related)} related songs for: {video_id}")
            return related
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canciones relacionadas de {video_id}")
    
    @cache_result(ttl=86400)
    async def get_lyrics(self, browse_id: str) -> Dict[str, Any]:
        """
        Get song lyrics.
        
        Args:
            browse_id: Lyrics browse ID.
        
        Returns:
            Lyrics dictionary.
        """
        self._log_operation("get_lyrics", browse_id=browse_id)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_lyrics, browse_id)
            lyrics = result if result is not None else {}
            self.logger.info(f"Retrieved lyrics for: {browse_id}")
            return lyrics
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener letras {browse_id}")
