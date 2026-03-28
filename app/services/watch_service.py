"""Service for watch playlists."""
from typing import Optional, Dict, Any, List
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.core.cache import cache_result


class WatchService(BaseService):
    """Service for watch playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the watch service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    @cache_result(ttl=3600)
    async def get_watch_playlist(
        self,
        video_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
        limit: int = 25,
        radio: bool = False,
        shuffle: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Get watch playlist (next songs when playing) with standardized pagination.

        Args:
            video_id: Video ID to start from.
            playlist_id: Playlist ID.
            limit: Maximum number of tracks (from ytmusicapi).
            radio: Generate radio playlist.
            shuffle: Shuffle the playlist.
            page: Current page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Watch playlist with standardized pagination metadata.
        """
        self._log_operation(
            "get_watch_playlist", 
            video_id=video_id, 
            playlist_id=playlist_id,
            radio=radio,
            shuffle=shuffle,
            page=page
        )

        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_watch_playlist,
                videoId=video_id,
                playlistId=playlist_id,
                limit=limit,
                radio=radio,
                shuffle=shuffle
            )

            if result is None:
                return {
                    "items": [],
                    "pagination": {
                        "total_results": 0,
                        "total_pages": 0,
                        "page": page,
                        "page_size": page_size,
                        "start_index": 0,
                        "end_index": 0,
                        "has_next": False,
                        "has_prev": False
                    }
                }

            # Extract and standardize tracks
            tracks = result.get('tracks', [])
            standardized_tracks = [
                ResponseService.standardize_song_object(track, include_stream_url=False)
                for track in tracks
            ]

            # Apply standardized pagination
            paginated = PaginationService.paginate(
                standardized_tracks,
                page=page,
                page_size=page_size
            )

            # Build response with watch playlist metadata
            response = {
                "watch_playlist_metadata": {
                    "title": result.get('title', ''),
                    "playlist_id": result.get('playlistId', ''),
                },
                "items": paginated['items'],
                "pagination": paginated['pagination']
            }

            self.logger.info(
                f"Retrieved watch playlist: {len(paginated['items'])} tracks "
                f"(video_id={video_id}, playlist_id={playlist_id}, page={page})"
            )
            return response

        except Exception as e:
            raise self._handle_ytmusic_error(
                e, 
                f"obtener watch playlist (video_id: {video_id}, playlist_id: {playlist_id})"
            )
