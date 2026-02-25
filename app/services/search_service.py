"""Service for searching YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
from ytmusicapi.exceptions import YTMusicServerError
import asyncio
import json
from app.core.cache import cache_result


class SearchService:
    """Service for searching music content."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
    def _handle_ytmusic_error(self, error: Exception, operation: str):
        """Handle ytmusicapi errors and provide better error messages."""
        error_msg = str(error)
        error_type = type(error).__name__
        
        if "Expecting value" in error_msg or "JSON" in error_msg or "line 1 column 1" in error_msg or "JSONDecodeError" in error_type:
            raise Exception(
                f"Error de autenticación o respuesta inválida de YouTube Music. "
                f"Verifica que browser.json sea válido y no esté expirado. "
                f"Operación: {operation}. "
                f"Error original: {error_msg}"
            )
        
        if "rate" in error_msg.lower() or "429" in error_msg:
            raise Exception(
                f"Rate limit de YouTube Music. Intenta más tarde. "
                f"Operación: {operation}"
            )
        
        raise Exception(f"Error en {operation}: {error_msg}")
    
    @cache_result(ttl=1800)
    async def search(
        self,
        query: str,
        filter: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 20,
        ignore_spelling: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for content."""
        try:
            result = await asyncio.to_thread(
                self.ytmusic.search,
                query=query,
                filter=filter,
                scope=scope,
                limit=limit,
                ignore_spelling=ignore_spelling
            )
            
            if result is None:
                return []
            
            if not isinstance(result, list):
                raise Exception(f"Respuesta inesperada de ytmusicapi.search: {type(result)}")
            
            return result
        except json.JSONDecodeError as e:
            error_msg = str(e)
            raise Exception(
                f"Error de autenticación o respuesta inválida de YouTube Music. "
                f"Verifica que browser.json sea válido y no esté expirado. "
                f"Operación: búsqueda '{query}'. "
                f"Error JSON: {error_msg}"
            )
        except ValueError as e:
            error_msg = str(e)
            if "Expecting value" in error_msg or "line 1 column 1" in error_msg:
                raise Exception(
                    f"Error de autenticación o respuesta inválida de YouTube Music. "
                    f"Verifica que browser.json sea válido y no esté expirado. "
                    f"Operación: búsqueda '{query}'. "
                    f"Error: {error_msg}"
                )
            raise self._handle_ytmusic_error(e, f"búsqueda '{query}'")
        except YTMusicServerError as e:
            raise self._handle_ytmusic_error(e, f"búsqueda '{query}'")
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            if "Expecting value" in error_msg or "line 1 column 1" in error_msg or "JSONDecodeError" in error_type:
                raise Exception(
                    f"Error de autenticación o respuesta inválida de YouTube Music. "
                    f"Verifica que browser.json sea válido y no esté expirado. "
                    f"Operación: búsqueda '{query}'. "
                    f"Error: {error_msg}"
                )
            raise self._handle_ytmusic_error(e, f"búsqueda '{query}'")
    
    @cache_result(ttl=3600)
    async def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions."""
        try:
            result = await asyncio.to_thread(self.ytmusic.get_search_suggestions, query)
            return result if result is not None else []
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"sugerencias para '{query}'")
    
    async def remove_search_suggestions(self, query: str) -> bool:
        """Remove search suggestions."""
        try:
            return await asyncio.to_thread(self.ytmusic.remove_search_suggestions, query)
        except Exception as e:
            raise self._handle_ytmusic_error(e, f"eliminar sugerencia '{query}'")
