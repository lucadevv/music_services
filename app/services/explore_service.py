"""Service for exploring YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio
import json
from app.core.cache import cache_result


class ExploreService:
    """Service for exploring music content."""
    
    KNOWN_GENRES = {
        "ggMPOg1uX3hRRFdlaEhHU09k": "Cumbia",
    }
    
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
    
    @cache_result(ttl=86400)
    async def get_mood_categories(self) -> Dict[str, Any]:
        """Get mood categories."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_mood_categories)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, "obtener categorías de moods")
    
    @cache_result(ttl=3600)
    async def get_mood_playlists(self, params: str) -> List[Dict[str, Any]]:
        """Get mood playlists for a given category."""
        try:
            return await asyncio.to_thread(self.ytmusic.get_mood_playlists, params)
        except KeyError as e:
            error_msg = str(e)
            if 'musicTwoRowItemRenderer' in error_msg or 'renderer' in error_msg.lower():
                raise Exception(
                    f"Error al parsear la respuesta de YouTube Music. "
                    f"Params usado: {params}. "
                    f"Intenta actualizar ytmusicapi o usar otro método."
                )
            raise
        except Exception as e:
            raise Exception(f"Error obteniendo playlists del mood/genre: {str(e)}. Params: {params}")
    
    def _find_genre_in_structure(self, data: Any, params: str) -> Optional[str]:
        """Recursively search for genre name in nested structure."""
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
        """Get genre name from params by searching in categories."""
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
            print(f"Error buscando género: {e}")
        
        return None
    
    @cache_result(ttl=3600)
    async def get_mood_playlists_alternative(
        self,
        genre_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Alternative method to get playlists by searching for genre name."""
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
        
        return unique_results[:limit]
    
    @cache_result(ttl=1800)
    async def get_charts(self, country: Optional[str] = None) -> Dict[str, Any]:
        """Get charts."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_charts, country)
            return result if result is not None else {}
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener charts (país: {country or 'global'})")
    
    @cache_result(ttl=3600)
    async def get_home_with_moods(self) -> Dict[str, Any]:
        """Get home page with moods extracted."""
        try:
            home = await asyncio.to_thread(self.ytmusic.get_home)
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
        
        return {
            "home": home,
            "moods": moods
        }
