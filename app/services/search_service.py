"""Service for searching YouTube Music content."""
from typing import Optional, List, Dict, Any
from ytmusicapi import YTMusic
import asyncio
from app.core.cache import cache_result


class SearchService:
    """Service for searching music content."""
    
    def __init__(self, ytmusic: YTMusic):
        self.ytmusic = ytmusic
    
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
        return await asyncio.to_thread(
            self.ytmusic.search,
            query=query,
            filter=filter,
            scope=scope,
            limit=limit,
            ignore_spelling=ignore_spelling
        )
    
    @cache_result(ttl=3600)
    async def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions."""
        return await asyncio.to_thread(self.ytmusic.get_search_suggestions, query)
    
    async def remove_search_suggestions(self, query: str) -> bool:
        """Remove search suggestions."""
        return await asyncio.to_thread(self.ytmusic.remove_search_suggestions, query)
