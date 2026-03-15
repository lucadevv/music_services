"""
Background tasks for cache management.
- Refresh expiring stream URLs before they expire
- Pre-cache popular content on startup
- Monitor cache health
"""
import asyncio
import logging
import time
from typing import List, Set
from datetime import datetime, timedelta

from app.services.stream_service import StreamService
from app.services.explore_service import ExploreService
from app.services.search_service import SearchService
from app.services.browse_service import BrowseService
from app.core.cache_redis import (
    get_cached_value,
    get_cached_timestamp,
    has_cached_key,
    get_cache_stats,
    get_active_streams,
    set_cached_value,
)
from app.core.ytmusic_client import get_ytmusic

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gestor de cache en background para mantener las URLs siempre frescas.
    
    Funcionalidades:
    1. Pre-cargar contenido popular al iniciar
    2. Refrescar URLs antes de que expiren (1 hora antes)
    3. Limitar requests a YouTube para evitar rate limiting
    """
    
    def __init__(self):
        self.stream_service = StreamService()
        self.explore_service = None
        self._running = False
        self._refresh_interval = 1800  # 30 minutos
        self._refresh_threshold = 3600  # 1 hora antes de expirar
        self._max_refresh_per_cycle = 20  # Max URLs a refrescar por ciclo
        self._processed_video_ids: Set[str] = set()  # Evitar duplicados en ciclo
        
        # Track metrics
        self.metrics = {
            "total_refreshes": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "cache_hits": 0,
            "last_full_refresh": None,
            "endpoint_warming": 0,
        }
    
    async def start(self):
        if self._running:
            return
        
        self._running = True
        logger.info("Starting Cache Manager...")
        
        await self._warm_cache()
        await self._warm_endpoint_cache()
        
        asyncio.create_task(self._background_refresh_loop())
        
        logger.info("Cache Manager started")
    
    async def stop(self):
        self._running = False
        logger.info("Stopping Cache Manager...")
    
    async def _warm_cache(self):
        logger.info("Warming cache with popular content...")
        
        popular_video_ids = [
            "dQw4w9WgXcQ",
            "jfKfPfyJRdk",
            "kJQP7kiw5Fk",
            "L_jWHffIx5E",
            "CevxZvSJLk8",
        ]
        
        logger.info(f"Pre-caching {len(popular_video_ids)} popular videos...")
        
        cached = 0
        for vid in popular_video_ids:
            try:
                await self.stream_service.get_stream_url(vid)
                cached += 1
                self.metrics["cache_hits"] += 1
            except Exception as e:
                logger.debug(f"Cache warming error for {vid}: {e}")
        
        self.metrics["last_full_refresh"] = datetime.now().isoformat()
        logger.info(f"Cache warming complete. Cached: {cached} videos")
    
    async def _warm_endpoint_cache(self):
        """Pre-cache popular endpoints on startup."""
        logger.info("Warming endpoint cache...")
        
        ytmusic = get_ytmusic()
        explore_svc = ExploreService(ytmusic)
        browse_svc = BrowseService(ytmusic)
        search_svc = SearchService(ytmusic)
        
        endpoints_cached = 0
        
        # Cache explore/moods categories
        try:
            cache_key = "music:endpoint:explore:moods:categories"
            if not await has_cached_key(cache_key):
                categories = await explore_svc.get_mood_categories()
                await set_cached_value(cache_key, {
                    "categories": categories,
                    "structure": "Cached at startup"
                }, ttl=1800)
                endpoints_cached += 1
                logger.info("Cached: /explore/moods categories")
        except Exception as e:
            logger.debug(f"Failed to cache explore/moods: {e}")
        
        # Cache explore charts
        try:
            cache_key = "music:endpoint:charts:global:False"
            if not await has_cached_key(cache_key):
                charts = await explore_svc.get_charts()
                await set_cached_value(cache_key, charts, ttl=600)
                endpoints_cached += 1
                logger.info("Cached: /explore/charts")
        except Exception as e:
            logger.debug(f"Failed to cache explore/charts: {e}")
        
        # Cache browse home
        try:
            cache_key = "music:endpoint:browse:home"
            if not await has_cached_key(cache_key):
                home = await browse_svc.get_home()
                await set_cached_value(cache_key, home, ttl=1800)
                endpoints_cached += 1
                logger.info("Cached: /browse/home")
        except Exception as e:
            logger.debug(f"Failed to cache browse/home: {e}")
        
        # Cache search suggestions for common queries
        common_queries = ["rock", "pop", "cumbia", "salsa", "reggaeton", "latin", "trap"]
        for q in common_queries:
            try:
                cache_key = f"music:endpoint:search:suggestions:{q}"
                if not await has_cached_key(cache_key):
                    suggestions = await search_svc.get_search_suggestions(q)
                    await set_cached_value(cache_key, {"suggestions": suggestions}, ttl=600)
                    endpoints_cached += 1
            except Exception as e:
                logger.debug(f"Failed to cache search suggestions for {q}: {e}")
        
        self.metrics["endpoint_warming"] = endpoints_cached
        logger.info(f"Endpoint cache warming complete. Cached: {endpoints_cached} endpoints")
    
    async def _background_refresh_loop(self):
        logger.info("Starting background refresh loop...")
        
        while self._running:
            try:
                await asyncio.sleep(self._refresh_interval)
                
                if not self._running:
                    break
                
                await self._refresh_expiring_urls()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background refresh error: {e}")
        
        logger.info("Background refresh loop stopped")
    
    async def _refresh_expiring_urls(self):
        try:
            stats = await get_cache_stats()
            logger.info(f"Cache stats: {stats.get('keys_count', 0)} keys")
            
            # Get active streams (videos people are listening to)
            active_streams = await get_active_streams(max_idle_time=3600, limit=50)
            
            if not active_streams:
                logger.info("No active streams to refresh")
                return
            
            # Reset processed set for this cycle
            self._processed_video_ids.clear()
            
            refreshed = 0
            for vid in active_streams:
                if refreshed >= self._max_refresh_per_cycle:
                    break
                
                if vid in self._processed_video_ids:
                    continue
                
                try:
                    cache_key = f"music:stream:url:{vid}"
                    
                    if await has_cached_key(cache_key):
                        timestamp = await get_cached_timestamp(cache_key)
                        elapsed = time.time() - timestamp
                        ttl_remaining = self.stream_service.STREAM_URL_TTL - elapsed
                        
                        # Refresh if less than 1 hour remaining
                        if ttl_remaining < self._refresh_threshold:
                            logger.info(f"Refreshing {vid} (ttl remaining: {int(ttl_remaining/60)}min)")
                            await self.stream_service.get_stream_url(vid, bypass_cache=True)
                            refreshed += 1
                            self.metrics["successful_refreshes"] += 1
                    
                    self._processed_video_ids.add(vid)
                
                except Exception as e:
                    logger.debug(f"Refresh error for {vid}: {e}")
                    self.metrics["failed_refreshes"] += 1
            
            self.metrics["total_refreshes"] += refreshed
            
            if refreshed > 0:
                logger.info(f"Refreshed {refreshed} URLs")
            
        except Exception as e:
            logger.error(f"Error in _refresh_expiring_urls: {e}")
    
    def get_metrics(self) -> dict:
        return {
            **self.metrics,
            "running": self._running,
            "refresh_interval": self._refresh_interval,
        }


cache_manager = CacheManager()
