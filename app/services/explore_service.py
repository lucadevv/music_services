"""Service for exploring YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio

from app.services.base_service import BaseService
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.core.cache import cache_result
from app.core.exceptions import ResourceNotFoundError, ExternalServiceError


class ExploreService(BaseService):
    """Service for exploring music content."""
    
    KNOWN_GENRES = {
        "ggMPOg1uX3hRRFdlaEhHU09k": "Cumbia",
    }
    
    def __init__(self, ytmusic: YTMusic):
        """
        Initialize the explore service.
        
        Args:
            ytmusic: YTMusic client instance.
        """
        super().__init__(ytmusic)
    
    @cache_result(ttl=86400)
    async def get_mood_categories(self) -> Dict[str, Any]:
        """
        Get mood categories.
        
        Returns:
            Dictionary of mood categories.
        """
        self._log_operation("get_mood_categories")
        
        try:
            result = await self._call_ytmusic(self.ytmusic.get_mood_categories)
            categories = result if result is not None else {}
            self.logger.info(f"Retrieved {len(categories)} mood categories")
            return categories
        except Exception as e:
            raise self._handle_ytmusic_error(e, "obtener categorías de moods")
    
    @cache_result(ttl=3600)
    async def get_mood_playlists(
        self,
        params: str,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get mood playlists for a given category with pagination.

        Args:
            params: Category parameters
            page: Current page number (default: 1)
            page_size: Number of playlists per page (default: 10, max: 50)
            max_page_size: Maximum allowed page size

        Returns:
            Playlists with pagination metadata
        """
        self._log_operation("get_mood_playlists", params=params, page=page, page_size=page_size)

        try:
            result = await self._call_ytmusic(self.ytmusic.get_mood_playlists, params)
            
            # Validate result is a list - ytmusicapi might return unexpected types
            if not isinstance(result, list):
                self.logger.warning(f"get_mood_playlists returned {type(result).__name__}, expected list: {result}")
                playlists = []
            else:
                playlists = result

            # Standardize playlists - they have playlistId, not videoId
            # Don't use standardize_song_object which requires videoId
            standardized_playlists = []
            for playlist in playlists:
                # Skip non-dict items - ytmusicapi might return strings or other types
                if not isinstance(playlist, dict):
                    self.logger.warning(f"Skipping non-dict playlist item: {type(playlist).__name__}: {playlist}")
                    continue
                if playlist.get("playlistId") or playlist.get("browseId"):
                    standardized_playlists.append({
                        "playlist_id": playlist.get("playlistId"),
                        "browse_id": playlist.get("browseId"),
                        "title": playlist.get("title", ""),
                        "thumbnails": playlist.get("thumbnails", []),
                        "thumbnail": playlist.get("thumbnails", [{}])[0].get("url") if playlist.get("thumbnails") else None,
                        "description": playlist.get("description", ""),
                        "author": playlist.get("author", []),
                        "count": playlist.get("count"),
                    })

            # Paginate
            paginated = PaginationService.paginate(
                standardized_playlists,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size
            )

            self.logger.info(f"Retrieved mood playlists for params: {params}")
            return paginated

        except (KeyError, TypeError, AttributeError) as e:
            error_msg = str(e)
            # Check for the specific 'str' object error
            if "'str' object" in error_msg and "has no attribute 'get'" in error_msg:
                self.logger.error(
                    f"get_mood_playlists received string instead of dict (params={params}). "
                    f"YouTube Music puede estar retornando datos inválidos."
                )
                raise ExternalServiceError(
                    message="YouTube Music retornó datos inválidos para esta categoría.",
                    details={"params": params, "error": "Expected dict, got string"}
                )
            if 'musicTwoRowItemRenderer' in error_msg or 'renderer' in error_msg.lower():
                raise ExternalServiceError(
                    message="Error al parsear la respuesta de YouTube Music.",
                    details={"params": params, "hint": "Intenta actualizar ytmusicapi o usar otro método."}
                )
            self.logger.error(
                f"get_mood_playlists error (params={params}): {error_msg}"
            )
            raise ExternalServiceError(
                message="Error al interpretar la respuesta de YouTube Music para este mood.",
                details={"params": params}
            )
        except Exception as e:
            error_msg = str(e).lower()
            is_not_found = any(kw in error_msg for kw in [
                '404', 'not found', 'no encontrado', 'does not exist',
                'requested entity was not found'
            ])
            if is_not_found:
                raise ResourceNotFoundError(
                    message=f"Categoría no encontrada para los parámetros proporcionados.",
                    details={"params": params, "resource_type": "mood_category"}
                )
            raise self._handle_ytmusic_error(e, f"obtener playlists del mood/genre (params: {params})")
    
    def _find_genre_in_structure(self, data: Any, params: str) -> Optional[str]:
        """
        Recursively search for genre name in nested structure.
        
        Args:
            data: Data structure to search.
            params: Params to match.
        
        Returns:
            Genre name if found, None otherwise.
        """
        if isinstance(data, dict):
            if data.get('params') == params:
                return data.get('title') or data.get('name')
            for value in data.values():
                result = self._find_genre_in_structure(value, params)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_genre_in_structure(item, params)
                if result:
                    return result
        return None
    
    async def get_genre_name_from_params(self, params: str) -> Optional[str]:
        """
        Get genre name from params by searching in categories.
        
        Args:
            params: Category parameters.
        
        Returns:
            Genre name if found, None otherwise.
        """
        if params in self.KNOWN_GENRES:
            return self.KNOWN_GENRES[params]
        
        try:
            categories = await self.get_mood_categories()
            if isinstance(categories, dict):
                for section_items in categories.values():
                    if isinstance(section_items, list):
                        for item in section_items:
                            if isinstance(item, dict) and item.get('params') == params:
                                return item.get('title')
            
            genre_name = self._find_genre_in_structure(categories, params)
            if genre_name:
                return genre_name
            
            home_data = await self.get_home_with_moods()
            genre_name = self._find_genre_in_structure(home_data, params)
            if genre_name:
                return genre_name
        except Exception as e:
            self.logger.warning(f"Error searching for genre: {e}")
        
        return None
    
    @cache_result(ttl=3600)
    async def get_mood_playlists_alternative(
        self,
        genre_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Alternative method to get playlists by searching for genre name.
        
        Args:
            genre_name: Genre name to search for.
            limit: Maximum number of results.
        
        Returns:
            List of playlists.
        """
        self._log_operation("get_mood_playlists_alternative", genre_name=genre_name)
        
        from app.services.search_service import SearchService
        search_service = SearchService(self.ytmusic)
        
        queries = [
            f"{genre_name} playlist",
            f"{genre_name} music",
            f"best {genre_name} songs"
        ]
        
        all_results = []
        for query in queries:
            try:
                results = await search_service.search(
                    query=query,
                    filter="playlists",
                    limit=limit // len(queries) + 1
                )
                if results:
                    all_results.extend(results)
                    if len(all_results) >= limit:
                        break
            except Exception:
                continue
        
        seen_ids = set()
        unique_results = []
        for item in all_results:
            playlist_id = item.get('playlistId') or item.get('browseId')
            if playlist_id and playlist_id not in seen_ids:
                seen_ids.add(playlist_id)
                unique_results.append(item)
            if len(unique_results) >= limit:
                break
        
        self.logger.info(f"Alternative search found {len(unique_results)} playlists for '{genre_name}'")
        return unique_results[:limit]
    
    @cache_result(ttl=1800)
    async def get_charts(
        self,
        country: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get charts with pagination.

        Args:
            country: Country code (optional)
            page: Current page number (default: 1)
            page_size: Number of songs per page (default: 10, max: 50)
            max_page_size: Maximum allowed page size

        Returns:
            Charts with paginated songs
        """
        self._log_operation("get_charts", country=country, page=page, page_size=page_size)

        try:
            result = await self._call_ytmusic(self.ytmusic.get_charts, country)
            charts = result if result is not None else {}

            # Debug: log the keys to understand structure
            self.logger.debug(f"Charts result keys: {list(charts.keys())}")

            # Extract items based on ytmusicapi schema:
            # - videos: Daily Top Music Videos (has playlistId, not videoId) -> use as trending
            # - artists: Top Artists (has browseId)
            # - genres: Featured Genres (has playlistId)
            # Note: top_songs might be in videos or as separate key
            raw_items = charts.get('videos') or []
            
            # If videos is empty, try top_songs
            if not raw_items:
                raw_items = charts.get('top_songs') or []

            # Standardize - handle both songs (videoId) and playlists (playlistId)
            standardized_items = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                    
                if item.get("videoId"):
                    # It's a song
                    try:
                        standardized_items.append(
                            ResponseService.standardize_song_object(item, include_stream_url=True)
                        )
                    except (ValueError, AttributeError, TypeError) as e:
                        self.logger.warning(f"Failed to standardize chart item: {e}")
                        continue
                elif item.get("playlistId"):
                    # It's a playlist (Daily Top Videos) - keep as trending item
                    standardized_items.append({
                        "playlist_id": item.get("playlistId"),
                        "browse_id": item.get("browseId"),
                        "title": item.get("title", ""),
                        "thumbnails": item.get("thumbnails", []),
                        "thumbnail": item.get("thumbnails", [{}])[0].get("url") if item.get("thumbnails") else None,
                        "description": item.get("description", ""),
                    })
                else:
                    # Keep other items as-is
                    standardized_items.append(item)

            # Extract artists and genres
            artists = charts.get('artists', [])
            genres = charts.get('genres', [])

            # Paginate
            paginated = PaginationService.paginate(
                standardized_items,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size
            )

            return {
                "charts": paginated,
                "trending": standardized_items[:page_size],  # Include raw trending for convenience
                "country": country or "global",
                "artists": artists,
                "genres": genres
            }

        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener charts (país: {country or 'global'})")
    
    @cache_result(ttl=3600)
    async def get_home_with_moods(self) -> Dict[str, Any]:
        """
        Get home page with moods extracted.
        
        Returns:
            Dictionary with home content and moods.
        """
        self._log_operation("get_home_with_moods")
        
        try:
            home = await self._call_ytmusic(self.ytmusic.get_home)
            if home is None:
                home = []
        except Exception as e:
            raise self._handle_ytmusic_error(e, "obtener home con moods")
        
        moods = []
        
        for item in home:
            title = item.get('title', '').lower()
            if 'mood' in title or 'genre' in title:
                moods = item.get('contents', [])
                break
        
        if not moods:
            try:
                mood_categories = await self.get_mood_categories()
                if isinstance(mood_categories, dict):
                    for section_items in mood_categories.values():
                        if isinstance(section_items, list):
                            moods.extend(section_items)
            except Exception:
                pass
        
        self.logger.info(f"Retrieved home with {len(moods)} moods")
        return {
            "home": home,
            "moods": moods
        }
