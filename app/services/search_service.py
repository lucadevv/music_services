"""Service for searching YouTube Music content."""
from typing import Optional, List, Dict, Any, Union
from ytmusicapi import YTMusic
from math import ceil
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.core.cache import cache_result
from app.core.circuit_breaker import youtube_search_circuit
from app.core.exceptions import (
    CircuitBreakerError,
    ResourceNotFoundError,
    ExternalServiceError,
)


class SearchService(BaseService):
    """Service for searching music content."""
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the search service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker is open and raise error if so."""
        if youtube_search_circuit.is_open():
            status = youtube_search_circuit.get_status()
            raise CircuitBreakerError(
                f"YouTube search temporarily unavailable. Retry in {status.get('remaining_time_seconds', 60)} seconds.",
                retry_after=status.get('remaining_time_seconds', 60)
            )
    
    @cache_result(ttl=1800)
    async def search(
        self,
        query: str,
        filter: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 20,
        ignore_spelling: bool = False,
        start_index: int = 0,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Search for content on YouTube Music with standardized pagination.

        Args:
            query: Search query string.
            filter: Filter type (songs, videos, albums, artists, playlists).
            scope: Search scope.
            limit: Maximum number of results.
            ignore_spelling: Whether to ignore spelling suggestions.
            start_index: Starting index for pagination (0-based).
            page: Current page number (default: 1)
            page_size: Number of items per page (default: 10)

        Returns:
            Search results with standardized pagination metadata.
        """
        self._log_operation("search", query=query, filter=filter, limit=limit, start_index=start_index, page=page, page_size=page_size)

        # Check circuit breaker before making request
        self._check_circuit_breaker()

        # Validate and normalize pagination params
        # Use page_size for pagination, but limit for ytmusicapi request
        validated_limit, validated_page, validated_start = PaginationService.validate_pagination_params(
            limit=page_size if page_size else limit,
            start_index=start_index
        )

        try:
            result = await self._call_ytmusic(
                self.ytmusic.search,
                query=query,
                filter=filter,
                scope=scope,
                limit=limit,
                ignore_spelling=ignore_spelling
            )

            # Record success
            youtube_search_circuit.record_success()

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

            if not isinstance(result, list):
                raise Exception(f"Respuesta inesperada de ytmusicapi.search: {type(result)}")

            # Standardize results based on their type
            standardized_results = []
            for item in result:
                if not isinstance(item, dict):
                    continue
                
                # Check if it's a song/video (has videoId)
                video_id = item.get("videoId") or item.get("video_id")
                
                if video_id:
                    try:
                        # Standardize but DONT try to fetch stream_url yet
                        # Fetching here would be sequential and slow
                        std_item = ResponseService.standardize_song_object(item, include_stream_url=True)
                        standardized_results.append(std_item)
                    except Exception as e:
                        self.logger.warning(f"Standardization failed: {e}")
                        standardized_results.append(item)
                else:
                    # Artists, albums, etc.
                    standardized_results.append(item)

            # Apply pagination
            paginated = PaginationService.paginate(
                standardized_results,
                page=validated_page,
                page_size=validated_limit
            )

            self.logger.info(f"Search completed for '{query}': {len(paginated['items'])} results")
            return paginated

        except CircuitBreakerError:
            raise
        except Exception as e:
            # Record failure
            youtube_search_circuit.record_failure(str(e))
            raise self._handle_ytmusic_error(e, f"búsqueda '{query}'")
    
    @cache_result(ttl=3600)
    async def get_search_suggestions(
        self, query: str, detailed_runs: bool = False
    ) -> Union[List[str], List[Dict[str, Any]]]:
        """
        Get search suggestions (YTMusic.get_search_suggestions).

        Args:
            query: Partial search query.
            detailed_runs: If True, returns dict items required for remove_search_suggestions.

        Returns:
            List of strings, or list of dicts when detailed_runs=True.
        """
        self._log_operation(
            "get_search_suggestions", query=query, detailed_runs=detailed_runs
        )

        self._check_circuit_breaker()

        try:
            result = await self._call_ytmusic(
                self.ytmusic.get_search_suggestions, query, detailed_runs
            )
            suggestions = result if result is not None else []

            youtube_search_circuit.record_success()

            self.logger.debug(
                f"Got {len(suggestions)} suggestions for '{query}' (detailed={detailed_runs})"
            )
            return suggestions
        except CircuitBreakerError:
            raise
        except Exception as e:
            youtube_search_circuit.record_failure(str(e))
            raise self._handle_ytmusic_error(e, f"sugerencias para '{query}'")


