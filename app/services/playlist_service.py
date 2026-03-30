"""Service for playlists."""
from typing import Optional, Dict, Any, List
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.core.cache import cache_result
from app.core.exceptions import ResourceNotFoundError, YTMusicServiceException


class PlaylistService(BaseService):
    """Service for reading public playlists."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the playlist service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    def _normalize_playlist_id(self, playlist_id: str) -> str:
        """
        Normalize playlist ID - remove VL prefix if present.
        
        Args:
            playlist_id: Raw playlist ID.
        
        Returns:
            Normalized playlist ID.
        """
        if playlist_id.startswith('VL'):
            return playlist_id[2:]
        return playlist_id
    
    @cache_result(ttl=86400)
    async def get_playlist(
        self,
        playlist_id: str,
        limit: int = 100,
        related: bool = False,
        suggestions_limit: int = 0,
        start_index: int = 0,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Get playlist information with standardized pagination.

        Args:
            playlist_id: Playlist ID.
            limit: Maximum number of tracks to return (from ytmusicapi).
            related: Include related songs.
            suggestions_limit: Limit for suggestions.
            start_index: Starting index for pagination (0-based).
            page: Current page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Playlist with standardized pagination metadata.
        """
        normalized_id = self._normalize_playlist_id(playlist_id)
        self._log_operation("get_playlist", playlist_id=normalized_id, limit=limit, start_index=start_index, page=page)

        # Validate pagination params
        page_size, page, start_index = PaginationService.validate_pagination_params(
            limit=limit,
            start_index=start_index
        )

        try:
            result = await asyncio.to_thread(
                self.ytmusic.get_playlist,
                normalized_id,
                limit=limit,
                related=related,
                suggestions_limit=suggestions_limit
            )
            if result is None:
                raise ResourceNotFoundError(
                    message="Playlist no encontrada.",
                    details={"resource_type": "playlist", "playlist_id": playlist_id}
                )

            # Extract and standardize tracks
            tracks = result.get('tracks', [])
            standardized_tracks = [
                ResponseService.standardize_song_object(track, include_stream_url=True)
                for track in tracks
            ]

            # Apply standardized pagination
            paginated = PaginationService.paginate(
                standardized_tracks,
                page=page,
                page_size=page_size
            )

            # Build response with playlist metadata
            response = {
                "playlistId": result.get('id'),
                "title": result.get('title', ''),
                "description": result.get('description', ''),
                "author": {
                    "name": result.get('author', {}).get('name', '') if isinstance(result.get('author'), dict) else result.get('author', ''),
                    "id": result.get('author', {}).get('id') if isinstance(result.get('author'), dict) else None
                },
                "trackCount": result.get('trackCount'),
                "duration": result.get('duration'),
                "durationSeconds": result.get('duration_seconds'),
                "thumbnails": result.get('thumbnails', []),
                "thumbnail": result.get('thumbnails', [{}])[0].get('url') if result.get('thumbnails') else '',
                "views": result.get('views'),
                "year": result.get('year'),
                "privacy": result.get('privacy'),
                "tracks": paginated['items'],
                "items": paginated['items'],  # Keep for backward compatibility if needed
                "pagination": paginated['pagination']
            }

            track_count = len(paginated['items'])
            self.logger.info(f"Retrieved playlist {playlist_id}: {track_count} tracks (page={page}, page_size={page_size})")
            return response

        except YTMusicServiceException:
            raise
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener playlist {playlist_id}")
