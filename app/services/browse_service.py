"""Service for browsing YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio
import json
from app.core.cache import cache_result


class BrowseService:
    """Service for browsing music content."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    def _handle_ytmusic_error(self, error: Exception, operation: str) -> Exception:
        """Handle ytmusicapi errors and provide better error messages."""
        error_msg = str(error)
        
        if "Expecting value" in error_msg or "JSON" in error_msg or "line 1 column 1" in error_msg:
            return Exception(
                f"Error de autenticación o respuesta inválida de YouTube Music. "
                f"Verifica que browser.json sea válido y no esté expirado. "
                f"Operación: {operation}. "
                f"Error original: {error_msg}"
            )
        
        if "rate" in error_msg.lower() or "429" in error_msg:
            return Exception(
                f"Rate limit de YouTube Music. Intenta más tarde. "
                f"Operación: {operation}"
            )
        
        return Exception(f"Error en {operation}: {error_msg}")
    
    def _safe_call(self, func, *args, operation: str, **kwargs):
        """Safely call ytmusicapi method with error handling."""
        try:
            result = asyncio.to_thread(func, *args, **kwargs)
            return result
        except json.JSONDecodeError as e:
            raise self._handle_ytmusic_error(e, operation)
        except Exception as e:
            raise self._handle_ytmusic_error(e, operation)
    
    @cache_result(ttl=86400)
    async def get_home(self) -> List[Dict[str, Any]]:
        """Get home page content."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_home)
            return result if result is not None else []
        except Exception as e:
            raise self._handle_ytmusic_error(e, "obtener home")
    
    @cache_result(ttl=86400)
    async def get_artist(self, channel_id: str) -> Dict[str, Any]:
        """Get artist information."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_artist, channel_id)
            if result is None:
                raise Exception(f"Artista no encontrado: {channel_id}")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener artista {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_artist_albums(
        self, 
        channel_id: str, 
        params: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get artist albums."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_artist_albums, channel_id, params)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbumes de artista {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album information."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_album, album_id)
            if result is None:
                raise Exception(f"Álbum no encontrado: {album_id}")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbum {album_id}")
    
    @cache_result(ttl=86400)
    async def get_album_browse_id(self, album_id: str) -> Optional[str]:
        """Get album browse ID."""
        try:
            return await asyncio.to_thread(self.ytmusic.get_album_browse_id, album_id)
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener browse ID de álbum {album_id}")
    
    @cache_result(ttl=86400)
    async def get_song(self, video_id: str, signature_timestamp: Optional[int] = None) -> Dict[str, Any]:
        """Get song metadata."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_song, video_id, signature_timestamp)
            if result is None:
                raise Exception(f"Canción no encontrada: {video_id}")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canción {video_id}")
    
    @cache_result(ttl=3600)
    async def get_song_related(self, video_id: str) -> List[Dict[str, Any]]:
        """Get related songs."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_song_related, video_id)
            return result if result is not None else []
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canciones relacionadas de {video_id}")
    
    @cache_result(ttl=86400)
    async def get_lyrics(self, browse_id: str) -> Dict[str, Any]:
        """Get song lyrics."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_lyrics, browse_id)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener letras {browse_id}")
