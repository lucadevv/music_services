"""Service for searching YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
from math import ceil
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.core.cache import cache_result
from app.core.circuit_breaker import youtube_search_circuit
from app.core.exceptions import CircuitBreakerError


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
            result = await asyncio.to_thread(
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

            # Standardize results
            standardized_results = [
                ResponseService.standardize_song_object(item, include_stream_url=False)
                for item in result
            ]

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
    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions for a partial query.
        
        Args:
            query: Partial search query.
        
        Returns:
            List of suggestion strings.
        """
        self._log_operation("get_search_suggestions", query=query)
        
        # Check circuit breaker before making request
        self._check_circuit_breaker()
        
        try:
            result = await asyncio.to_thread(self.ytmusic.get_search_suggestions, query)
            suggestions = result if result is not None else []
            
            # Record success
            youtube_search_circuit.record_success()
            
            self.logger.debug(f"Got {len(suggestions)} suggestions for '{query}'")
            return suggestions
        except CircuitBreakerError:
            raise
        except Exception as e:
            # Record failure
            youtube_search_circuit.record_failure(str(e))
            raise self._handle_ytmusic_error(e, f"sugerencias para '{query}'")
    
    async def remove_search_suggestions(self, query: str) -> bool:
        """
        Remove a search suggestion from history.
        
        Args:
            query: Query to remove.
        
        Returns:
            True if successful.
        """
        self._log_operation("remove_search_suggestions", query=query)
        
        try:
            result = await asyncio.to_thread(self.ytmusic.remove_search_suggestions, query)
            self.logger.info(f"Removed search suggestion for '{query}'")
            return result
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"eliminar sugerencia '{query}'")
