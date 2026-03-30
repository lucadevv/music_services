"""Service for browsing YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
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
    async def get_home(
        self,
        limit: int = 20,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get home page content with pagination.

        Args:
            limit: Number of sections to retrieve from ytmusicapi (default: 20)
            page: Current page number (default: 1)
            page_size: Number of items per page (default: 10, max: 50)
            max_page_size: Maximum allowed page size

        Returns:
            Paginated home content with metadata
        """
        self._log_operation("get_home", page=page, page_size=page_size, limit=limit)

        try:
            result = await self._call_ytmusic(self.ytmusic.get_home, limit=limit)
            content = result if result is not None else []
            self.logger.info(f"Retrieved home page: {len(content)} sections")

            # Paginate content
            paginated = PaginationService.paginate(
                content,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size
            )

            return paginated

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
            result = await self._call_ytmusic(self.ytmusic.get_artist, channel_id)
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
        Get artist albums with fallback and retry logic.
        
        Args:
            channel_id: Artist channel ID.
            params: Pagination parameters.
        
        Returns:
            Artist albums dictionary.
        """
        self._log_operation("get_artist_albums", channel_id=channel_id)
        
        # Rate limit error handling
        rate_limit_keywords = ['429', 'rate limit', 'quota', 'too many requests']
        
        async def fetch_albums():
            return await self._call_ytmusic(self.ytmusic.get_artist_albums, channel_id, params)
        
        async def fetch_with_fallback():
            # First try: direct get_artist_albums call
            try:
                return await fetch_albums()
            except Exception as e:
                error_msg = str(e).lower()
                is_rate_limit = any(kw in error_msg for kw in rate_limit_keywords)
                if is_rate_limit:
                    self.logger.warning(f"Rate limit hit for artist {channel_id}: {e}")
                
                # Second try: get artist info to get the albums browse_id
                self.logger.debug(f"get_artist_albums failed, trying fallback with get_artist for {channel_id}")
                try:
                    artist_data = await asyncio.to_thread(self.ytmusic.get_artist, channel_id)
                    if artist_data:
                        # Try to get albums using the albums browse_id from artist response
                        albums_browse_id = artist_data.get("albums", {}).get("browseId")
                        if albums_browse_id:
                            # Use get_album_browse_id logic - call get_albums via browse endpoint
                            # Fallback: just return the artist data's albums section
                            albums_section = artist_data.get("albums", {})
                            self.logger.info(f"Retrieved albums via get_artist fallback for {channel_id}")
                            return albums_section
                except Exception as fallback_error:
                    self.logger.warning(f"Fallback also failed for {channel_id}: {fallback_error}")
                
                # If we get here, both failed - re-raise the original exception
                raise
        
        try:
            # Retry logic: attempt up to 2 times
            max_retries = 2
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    result = await fetch_with_fallback()
                    albums = result if result is not None else {}
                    self.logger.info(f"Retrieved albums for artist: {channel_id} (attempt {attempt + 1})")
                    return albums
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Attempt {attempt + 1} failed for {channel_id}: {e}, retrying...")
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
            # All retries exhausted
            raise last_error
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbumes de artista {channel_id}")
    
    @cache_result(ttl=86400)
    async def get_album(
        self,
        album_id: str,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get album information with pagination for tracks.

        Args:
            album_id: Album ID
            page: Current page number (default: 1)
            page_size: Number of tracks per page (default: 10, max: 50)
            max_page_size: Maximum allowed page size

        Returns:
            Album with paginated tracks
        """
        self._log_operation("get_album", album_id=album_id, page=page, page_size=page_size)

        try:
            result = await self._call_ytmusic(self.ytmusic.get_album, album_id)
            if result is None:
                raise ResourceNotFoundError(
                    message="Álbum no encontrado.",
                    details={"resource_type": "album", "album_id": album_id}
                )

            # Debug: log the keys in the result to understand structure
            self.logger.debug(f"Album result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")

            # Extract tracks - handle different possible keys
            # ytmusicapi returns tracks in 'tracks' key
            raw_tracks = result.get('tracks') or result.get('songs') or result.get('items', [])
            
            # If still empty, log warning - might be ytmusicapi returning empty tracks
            if not raw_tracks:
                self.logger.warning(f"No tracks found for album {album_id}. Result keys: {list(result.keys())}")
                raw_tracks = []

            # Standardize tracks - only standardize items that have videoId
            standardized_tracks = []
            for track in raw_tracks:
                # Skip non-dict items
                if not isinstance(track, dict):
                    continue
                if track.get("videoId"):
                    try:
                        standardized_tracks.append(
                            ResponseService.standardize_song_object(track, include_stream_url=True)
                        )
                    except (ValueError, AttributeError, TypeError) as e:
                        self.logger.warning(f"Failed to standardize track: {e}")
                        continue
                else:
                    # Keep tracks without videoId as-is (might be unavailable)
                    standardized_tracks.append(track)

            # Paginate tracks
            paginated = PaginationService.paginate(
                standardized_tracks,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size
            )

            # Add album metadata to response
            paginated["album_metadata"] = {
                "title": result.get('title', ''),
                "artists": result.get('artists', []),
                "year": result.get('year'),
                "duration": result.get('duration'),
                "num_tracks": len(raw_tracks)
            }

            self.logger.info(f"Retrieved album: {album_id} with {len(raw_tracks)} tracks")
            return paginated

        except YTMusicServiceException:
            # Re-raise custom exceptions directly
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener álbum {album_id}")
    
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
            
            # Fallback: try to get browse_id from get_album if ytmusicapi returns None
            if result is None:
                self.logger.debug(f"get_album_browse_id returned None, trying get_album fallback for {album_id}")
                album_data = await asyncio.to_thread(self.ytmusic.get_album, album_id)
                if album_data:
                    # Extract browse_id from audioPlaylistId if available
                    audio_playlist_id = album_data.get("audioPlaylistId")
                    if audio_playlist_id:
                        # audioPlaylistId is in format "OLAK5uy_xxxxx", we need the browse ID
                        result = audio_playlist_id
                        self.logger.debug(f"Extracted browse ID from album: {result}")
            
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
            result = await self._call_ytmusic(self.ytmusic.get_song, video_id, signature_timestamp)
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
    
    @staticmethod
    def _flatten_song_related_sections(sections: Any) -> List[Dict[str, Any]]:
        """ytmusicapi get_song_related returns shelved sections with title + contents lists."""
        flat: List[Dict[str, Any]] = []
        if not isinstance(sections, list):
            return flat
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            contents = sec.get("contents")
            if not isinstance(contents, list):
                continue
            for item in contents:
                if isinstance(item, dict) and item.get("videoId"):
                    flat.append(item)
        return flat

    @cache_result(ttl=3600)
    async def get_song_related(
        self,
        video_id: str,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get related songs with pagination.

        ytmusicapi: ``get_song_related(browseId)`` expects the ``related`` browse id from
        ``get_watch_playlist(video_id)``, not the raw video id.
        """
        self._log_operation("get_song_related", video_id=video_id, page=page, page_size=page_size)

        try:
            watch = await self._call_ytmusic(self.ytmusic.get_watch_playlist, video_id)
            if not watch:
                raise ResourceNotFoundError(
                    message="No se pudo obtener la playlist de reproducción para canciones relacionadas.",
                    details={"resource_type": "song", "video_id": video_id},
                )
            related_browse_id = watch.get("related")
            if not related_browse_id:
                self.logger.info(f"Watch playlist sin pestaña 'related' para video_id={video_id}")
                return PaginationService.paginate(
                    [],
                    page=page,
                    page_size=page_size,
                    max_page_size=max_page_size,
                )

            sections = await self._call_ytmusic(self.ytmusic.get_song_related, related_browse_id)
            related_songs = self._flatten_song_related_sections(sections)
            self.logger.info(f"Related songs flattened: {len(related_songs)} for video_id={video_id}")

            standardized_songs = [
                ResponseService.standardize_song_object(song, include_stream_url=True)
                for song in related_songs
            ]
            return PaginationService.paginate(
                standardized_songs,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size,
            )
        except YTMusicServiceException:
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener canciones relacionadas de {video_id}")
    
    @cache_result(ttl=86400)
    async def get_lyrics_by_video_id(self, video_id: str) -> Dict[str, Any]:
        """
        Get song lyrics by video ID.
        
        Args:
            video_id: YouTube video ID.
        
        Returns:
            Lyrics dictionary.
        """
        self._log_operation("get_lyrics_by_video_id", video_id=video_id)
        
        try:
            # First get the watch playlist to find the lyrics browse ID
            watch_playlist = await self._call_ytmusic(self.ytmusic.get_watch_playlist, video_id)
            
            # Check if watch playlist has lyrics
            if not watch_playlist:
                self.logger.info(f"No watch playlist for video: {video_id}")
                return {"lyrics": None, "source": None, "error": "No lyrics available"}
            
            # Get the lyrics browse ID from the watch playlist
            lyrics_browse_id = watch_playlist.get('lyrics')
            if not lyrics_browse_id:
                self.logger.info(f"No lyrics browse ID for video: {video_id}")
                return {"lyrics": None, "source": None, "error": "No lyrics available"}
            
            # Now get the actual lyrics
            result = await self._call_ytmusic(self.ytmusic.get_lyrics, lyrics_browse_id)
            lyrics = result if result is not None else {}
            self.logger.info(f"Retrieved lyrics for video: {video_id}")
            return lyrics
        except Exception as e:
            self.logger.warning(f"Could not get lyrics for {video_id}: {e}")
            return {"lyrics": None, "source": None, "error": str(e)}
    
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
            result = await self._call_ytmusic(self.ytmusic.get_lyrics, browse_id)
            lyrics = result if result is not None else {}
            self.logger.info(f"Retrieved lyrics for: {browse_id}")
            return lyrics
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener letras {browse_id}")
