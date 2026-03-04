"""
Background tasks for cache management.
- Refresh expiring stream URLs before they expire
- Pre-cache popular content on startup
- Monitor cache health
"""
import asyncio
import logging
from typing import List, Set
from datetime import datetime, timedelta

from app.services.stream_service import StreamService
from app.services.explore_service import ExploreService
from app.core.cache_redis import (
    get_cached_value,
    get_cached_timestamp,
    has_cached_key,
    get_cache_stats,
)
from app.core.ytmusic_client import get_ytmusic

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gestor de cache en background para mantener las URLs siempre frescas.
    
    Funcionalidades:
    1. Pre-cargar contenido popular al iniciar
    2. Refrescar URLs antes de que expiren
    3. Limitar requests a YouTube para evitar rate limiting
    """
    
    def __init__(self):
        self.stream_service = StreamService()
        # No inicializamos explore_service aquí - lo haremos en _warm_cache
        self.explore_service = None
        self._running = False
        self._refresh_interval = 600  # 10 minutos
        self._refresh_threshold = 1800  # 30 minutos antes de expirar
        self._max_refresh_per_cycle = 50  # Max URLs a refrescar por ciclo
        self._processed_video_ids: Set[str] = set()  # Evitar duplicados
        
        # Track metrics
        self.metrics = {
            "total_refreshes": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "cache_hits": 0,
            "last_full_refresh": None,
        }
    
    async def start(self):
        """Iniciar el gestor de cache en background."""
        if self._running:
            return
        
        self._running = True
        logger.info("🚀 Starting Cache Manager...")
        
        # 1. Cache warming: pre-cargar contenido popular
        await self._warm_cache()
        
        # 2. Iniciar loop de background refresh
        asyncio.create_task(self._background_refresh_loop())
        
        logger.info("✅ Cache Manager started")
    
    async def stop(self):
        """Detener el gestor de cache."""
        self._running = False
        logger.info("🛑 Stopping Cache Manager...")
    
    async def _warm_cache(self):
        """
        Pre-cargar contenido popular al iniciar.
        Esto hace que la primera solicitud sea instantánea.
        """
        logger.info("🔥 Warming cache with popular content...")
        
        # Videos populares已知 - Estos siempre funcionan
        popular_video_ids = [
            "dQw4w9WgXcQ",  # Rick Astley
            "9bZkp7q19f0",  # PSY - Gangnam Style
            "jfKfPfyJRdk",  # Lofi Girl
            "kJQP7kiw5Fk",  # Luis Fonsi
            "L_jWHffIx5E",  # Nirvana
            "3tmd-ClpJxA",  # Beatles
            "CevxZvSJLk8",  # Katy Perry
            "hT_nvWreIhg",  # Katy Perry
            "OPf0YbXqDm0",  # Uptown Funk
            "lYBUbBu4W0E",  # Queen
        ]
        
        logger.info(f"📥 Pre-caching {len(popular_video_ids)} popular videos...")
        
        # Cache en paralelo (sin bloquear)
        cached = 0
        for vid in popular_video_ids:
            try:
                await self.stream_service.get_stream_url(vid)
                cached += 1
                self.metrics["cache_hits"] += 1
            except Exception as e:
                logger.debug(f"Cache warming error for {vid}: {e}")
        
        self.metrics["last_full_refresh"] = datetime.now().isoformat()
        logger.info(f"✅ Cache warming complete. Cached: {cached} videos")
    
    async def _background_refresh_loop(self):
        """
        Loop de background que refresca URLs antes de que expiren.
        """
        logger.info("🔄 Starting background refresh loop...")
        
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
        
        logger.info("🛑 Background refresh loop stopped")
    
    async def _refresh_expiring_urls(self):
        """
        Refrescar URLs que están por expirar.
        Solo refresca si faltan menos de _refresh_threshold segundos.
        """
        try:
            # Obtener stats del cache
            stats = await get_cache_stats()
            logger.info(f"📊 Cache stats: {stats.get('keys_count', 0)} keys")
            
            # Buscar keys de stream URL que están por expirar
            # Este es un enfoque simple - en producción sería más eficiente
            
            # Por ahora, hacer refresh de videos populares conocidos
            popular_video_ids = [
                "dQw4w9WgXcQ",  # Rick Astley
                "9bZkp7q19f0",  # Gangnam Style
                "jfKfPfyJRdk",  # Lofi
                "kJQP7kiw5Fk",  # Despacito
                "L_jWHffIx5E",  # Smells Like Teen Spirit
            ]
            
            refreshed = 0
            for vid in popular_video_ids:
                if refreshed >= self._max_refresh_per_cycle:
                    break
                
                try:
                    # Verificar si está cacheado y por expirar
                    cache_key = f"music:stream:url:{vid}"
                    
                    if await has_cached_key(cache_key):
                        timestamp = await get_cached_timestamp(cache_key)
                        import time
                        elapsed = time.time() - timestamp
                        
                        # Si falta menos de 30 minutos, refresh
                        if elapsed > (6 * 3600 - self._refresh_threshold):
                            logger.info(f"🔄 Refreshing {vid} (elapsed: {int(elapsed/60)}min)")
                            await self.stream_service.get_stream_url(vid, bypass_cache=True)
                            refreshed += 1
                            self.metrics["successful_refreshes"] += 1
                
                except Exception as e:
                    logger.debug(f"Refresh error for {vid}: {e}")
                    self.metrics["failed_refreshes"] += 1
            
            self.metrics["total_refreshes"] += refreshed
            
            if refreshed > 0:
                logger.info(f"✅ Refreshed {refreshed} URLs")
            
        except Exception as e:
            logger.error(f"Error in _refresh_expiring_urls: {e}")
    
    def get_metrics(self) -> dict:
        """Obtener métricas del gestor de cache."""
        return {
            **self.metrics,
            "running": self._running,
            "refresh_interval": self._refresh_interval,
        }


# Instancia global del gestor de cache
cache_manager = CacheManager()
