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
            result = await asyncio.to_thread(self.ytmusic.get_home, limit=limit)
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
            return await asyncio.to_thread(self.ytmusic.get_artist_albums, channel_id, params)
        
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
            result = await asyncio.to_thread(self.ytmusic.get_album, album_id)
            if result is None:
                raise ResourceNotFoundError(
                    message="Álbum no encontrado.",
                    details={"resource_type": "album", "album_id": album_id}
                )

            # Extract tracks
            tracks = result.get('tracks') or result.get('songs', [])

            # Standardize tracks
            standardized_tracks = [
                ResponseService.standardize_song_object(track, include_stream_url=False)
                for track in tracks
            ]

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
                "num_tracks": len(tracks)
            }

            self.logger.info(f"Retrieved album: {album_id} with {len(tracks)} tracks")
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
    async def get_song_related(
        self,
        video_id: str,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get related songs with pagination.

        Args:
            video_id: Video ID
            page: Current page number (default: 1)
            page_size: Number of songs per page (default: 10, max: 50)
            max_page_size: Maximum allowed page size

        Returns:
            Related songs with pagination metadata
        """
        self._log_operation("get_song_related", video_id=video_id, page=page, page_size=page_size)

        # Keywords to detect rate limit / external service errors
        retry_keywords = ['429', 'rate limit', 'quota', 'too many requests', '500', '502', 'bad gateway', 'internal server error']

        async def fetch_related():
            return await asyncio.to_thread(self.ytmusic.get_song_related, video_id)
        
        async def fetch_with_fallback():
            # First try: direct get_song_related call
            try:
                return await fetch_related()
            except Exception as e:
                error_msg = str(e).lower()
                is_retryable = any(kw in error_msg for kw in retry_keywords)
                if is_retryable:
                    self.logger.warning(f"Retryable error for related songs {video_id}: {e}")
                
                # Second try: get song info to extract related content
                self.logger.debug(f"get_song_related failed, trying fallback with get_song for {video_id}")
                try:
                    song_data = await asyncio.to_thread(self.ytmusic.get_song, video_id)
                    if song_data:
                        # Try to extract related content from song response
                        related = song_data.get("related", [])
                        if related:
                            self.logger.info(f"Retrieved related songs via get_song fallback for {video_id}")
                            return related
                except Exception as fallback_error:
                    self.logger.warning(f"Fallback also failed for {video_id}: {fallback_error}")
                
                # If we get here, both failed - re-raise the original exception
                raise
        
        try:
            # Retry logic: attempt up to 2 times
            max_retries = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    result = await fetch_with_fallback()
                    related = result if result is not None else []
                    self.logger.info(f"Retrieved {len(related)} related songs for: {video_id} (attempt {attempt + 1})")

                    # Standardize songs
                    standardized_songs = [
                        ResponseService.standardize_song_object(song, include_stream_url=False)
                        for song in related
                    ]

                    # Paginate
                    paginated = PaginationService.paginate(
                        standardized_songs,
                        page=page,
                        page_size=page_size,
                        max_page_size=max_page_size
                    )

                    return paginated

                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Attempt {attempt + 1} failed for related {video_id}: {e}, retrying...")
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

            # All retries exhausted
            raise last_error
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
            watch_playlist = await asyncio.to_thread(self.ytmusic.get_watch_playlist, video_id)
            
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
            result = await asyncio.to_thread(self.ytmusic.get_lyrics, lyrics_browse_id)
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
            result = await asyncio.to_thread(self.ytmusic.get_lyrics, browse_id)
            lyrics = result if result is not None else {}
            self.logger.info(f"Retrieved lyrics for: {browse_id}")
            return lyrics
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener letras {browse_id}")
