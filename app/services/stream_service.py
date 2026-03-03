"""Service for streaming audio with Redis caching."""
import time
import random
import re
from typing import Optional, Dict, Any, List
import asyncio
import yt_dlp

from app.services.base_service import BaseService
from app.core.config import get_settings
from app.core.cache_redis import (
    get_cached_value,
    set_cached_value,
    get_cached_timestamp,
    has_cached_key,
)
from app.core.circuit_breaker import youtube_stream_circuit
from app.core.exceptions import (
    CircuitBreakerError,
    RateLimitError,
    ExternalServiceError,
    ValidationError,
)


class StreamService(BaseService):
    """Service for audio streaming with Redis caching."""
    
    # TTL para diferentes tipos de datos
    METADATA_TTL = 86400  # 24 horas - metadatos no cambian
    STREAM_URL_TTL = 14400  # 4 horas - URLs de stream duran más (aumentado de 2h)
    
    # Retry config
    MAX_RETRIES = 3
    BASE_DELAY = 2  # segundos
    
    def __init__(self):
        """Initialize the stream service."""
        super().__init__()
        self.settings = get_settings()
    
    def _get_metadata_cache_key(self, video_id: str) -> str:
        """Generate cache key for metadata."""
        return f"music:stream:metadata:{video_id}"
    
    def _get_stream_url_cache_key(self, video_id: str) -> str:
        """Generate cache key for stream URL."""
        return f"music:stream:url:{video_id}"
    
    async def _get_cached_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata if available and not expired (async)."""
        if not self.settings.CACHE_ENABLED:
            return None
        
        cache_key = self._get_metadata_cache_key(video_id)
        
        try:
            # Check if key exists
            if not await has_cached_key(cache_key):
                return None
            
            # Get timestamp
            timestamp = await get_cached_timestamp(cache_key)
            if timestamp > 0 and (time.time() - timestamp) < self.METADATA_TTL:
                cached_data = await get_cached_value(cache_key)
                if cached_data:
                    self.logger.info(f"✅ Cache HIT for metadata: {video_id}")
                    return cached_data
        except Exception as e:
            self.logger.warning(f"Error getting cached metadata: {e}")
        
        return None
    
    async def _get_cached_stream_url(self, video_id: str) -> Optional[str]:
        """Get cached stream URL if available and not expired (async)."""
        if not self.settings.CACHE_ENABLED:
            return None
        
        cache_key = self._get_stream_url_cache_key(video_id)
        
        try:
            # Check if key exists
            if not await has_cached_key(cache_key):
                self.logger.debug(f"Cache MISS (no key) for stream URL: {video_id}")
                return None
            
            # Get timestamp to check TTL
            timestamp = await get_cached_timestamp(cache_key)
            if timestamp > 0:
                elapsed = time.time() - timestamp
                if elapsed < self.STREAM_URL_TTL:
                    cached_url = await get_cached_value(cache_key)
                    if cached_url:
                        remaining = int(self.STREAM_URL_TTL - elapsed)
                        self.logger.info(f"✅ Cache HIT for stream URL: {video_id} (expires in {remaining}s)")
                        return cached_url
                    else:
                        self.logger.warning(f"Cache key exists but value is None for: {video_id}")
                else:
                    self.logger.debug(f"Cache EXPIRED for stream URL: {video_id} (elapsed: {int(elapsed)}s)")
            else:
                self.logger.debug(f"Cache has no timestamp for: {video_id}")
        except Exception as e:
            self.logger.warning(f"Error getting cached stream URL: {e}")
        
        return None
    
    async def _cache_metadata(self, video_id: str, metadata: Dict[str, Any]) -> None:
        """Cache metadata with long TTL (async)."""
        if not self.settings.CACHE_ENABLED:
            return
        
        cache_key = self._get_metadata_cache_key(video_id)
        try:
            await set_cached_value(cache_key, metadata, self.METADATA_TTL)
            self.logger.debug(f"Cached metadata for: {video_id} (TTL: {self.METADATA_TTL}s)")
        except Exception as e:
            self.logger.warning(f"Error caching metadata: {e}")
    
    async def _cache_stream_url(self, video_id: str, stream_url: str) -> None:
        """Cache stream URL with TTL (async)."""
        if not self.settings.CACHE_ENABLED:
            return
        
        cache_key = self._get_stream_url_cache_key(video_id)
        try:
            await set_cached_value(cache_key, stream_url, self.STREAM_URL_TTL)
            self.logger.info(f"💾 Cached stream URL for: {video_id} (TTL: {self.STREAM_URL_TTL}s)")
        except Exception as e:
            self.logger.warning(f"Error caching stream URL: {e}")

    async def get_stream_url(self, video_id: str, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Get audio stream URL with intelligent caching.
        
        Strategy:
        1. Check cached metadata (24 hours TTL)
        2. Check cached stream URL (2 hours TTL)
        3. If both cached and valid, return immediately (0 YouTube calls)
        4. If metadata cached but stream expired, refresh only stream URL
        5. If nothing cached, fetch everything from YouTube
        
        Args:
            video_id: Video ID.
            bypass_cache: If True, ignore cache and fetch fresh URL.
        
        Returns:
            Dictionary with stream URL and metadata.
        
        Raises:
            CircuitBreakerError: If circuit breaker is open.
            RateLimitError: If rate limited by YouTube.
            ExternalServiceError: If error fetching stream.
        """
        self._log_operation("get_stream_url", video_id=video_id)
        
        # Check circuit breaker first
        if youtube_stream_circuit.is_open():
            status = youtube_stream_circuit.get_status()
            raise CircuitBreakerError(
                message="Servicio temporalmente no disponible debido a sobrecarga.",
                details={
                    "retry_after": status['remaining_time_seconds'],
                    "state": status['state'],
                    "operation": "get_stream_url"
                }
            )
        
        # Try to get from cache first (unless bypass)
        if not bypass_cache:
            cached_metadata = await self._get_cached_metadata(video_id)
            cached_stream_url = await self._get_cached_stream_url(video_id)
            
            self.logger.info(f"🔍 Cache check for {video_id}: metadata={cached_metadata is not None}, url={cached_stream_url is not None}")
            
            if cached_metadata and cached_stream_url:
                self.logger.info(f"🎯 Fully cached response for: {video_id}")
                return {**cached_metadata, "streamUrl": cached_stream_url, "stream_url": cached_stream_url, "from_cache": True}
            elif cached_stream_url:
                # Stream URL cached but no metadata (shouldn't happen, but handle it)
                self.logger.info(f"⚡ Stream URL cached for: {video_id}")
                return {"streamUrl": cached_stream_url, "stream_url": cached_stream_url, "from_cache": True}
        
        self.logger.info(f"🔄 Fetching fresh stream URL for: {video_id} (bypass_cache={bypass_cache})")
        
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Configuración de yt-dlp para OBTENER MEJOR AUDIO
            # Primero intentar bestaudio, luego fallback a best
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                # Intentar mejor audio, luego mejor calidad disponible
                'format_sort': ['codec', 'br', 'size'],
                'format': 'bestaudio/best',
                'nocheckcertificate': True,
                'extractor_args': {
                    'youtube': {
                        # Android tiene mejores streams de audio
                        'player_client': ['android', 'web', 'default'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.youtube/19.02.39 (Linux; U; Android 13; en_US) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                },
                'socket_timeout': 60,
                'retries': 3,
                'check_runtime': False,
                'no_color': True,
                # No limitar a formatos específicos para obtener todos los formats
                'allow_unplayable_formats': True,
            }
            
            def extract_info_with_retry(attempt: int = 0) -> Dict[str, Any]:
                """Extract info with retry logic."""
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        return ydl.extract_info(video_url, download=False)
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Errores recuperables que merecen retry
                    recoverable = any(keyword in error_str for keyword in [
                        'timeout', 'connection', 'network', 'temporary failure',
                        'unable to extract', 'rate', '429'
                    ])
                    
                    if recoverable and attempt < self.MAX_RETRIES:
                        delay = self.BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                        self.logger.warning(f"Retry {attempt + 1}/{self.MAX_RETRIES} for {video_id} after {delay:.1f}s: {str(e)}")
                        time.sleep(delay)
                        return extract_info_with_retry(attempt + 1)
                    
                    self.logger.error(f"yt-dlp extraction error: {str(e)}")
                    raise
            
            info = await asyncio.to_thread(extract_info_with_retry)
            
            # Buscar formato de audio
            audio_url = None
            
            self.logger.info(f"📋 Available formats keys: {list(info.keys())}")
            
            # Helper function to check if format is audio-only
            def is_audio_only(f):
                acodec = f.get('acodec')
                vcodec = f.get('vcodec')
                # Audio-only if: has audio codec AND no video codec
                has_audio = acodec is not None and acodec != 'none' and acodec != ''
                has_video = vcodec is not None and vcodec != 'none' and vcodec != ''
                return has_audio and not has_video
            
            # Buscar formatos de audio
            formats = info.get('formats') or []
            
            audio_url = None
            for f in formats:
                if is_audio_only(f):
                    audio_url = f['url']
                    self.logger.info(f"✅ Found audio: itag={f.get('format_id')}, ext={f.get('ext')}")
                    break
            
            # Si no hay en formats, buscar en adaptive formats
            if not audio_url:
                adaptive_formats = info.get('adaptive_formats') or []
                for f in adaptive_formats:
                    if is_audio_only(f):
                        audio_url = f['url']
                        self.logger.info(f"✅ Found audio in adaptive: itag={f.get('format_id')}, ext={f.get('ext')}")
                        break
            
            # Último recurso - usar URL directa si ninguna otra funciónó
            if not audio_url:
                if info.get('url'):
                    audio_url = info['url']
                    self.logger.warning(f"⚠️ No audio-only format found, using direct URL")
            
            if not audio_url:
                self.logger.warning(f"yt-dlp could not get stream for: {video_id}")
                raise ExternalServiceError(
                    message="No se pudo obtener el stream de audio. Verifica el ID del video.",
                    details={"video_id": video_id, "operation": "get_stream_url"}
                )
            
            youtube_stream_circuit.record_success()
            
            # Extraer metadatos
            metadata = {
                "title": info.get('title'),
                "artist": info.get('artist', info.get('uploader', 'Unknown Artist')),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail')
            }
            
            # Cache both metadata and stream URL
            await self._cache_metadata(video_id, metadata)
            await self._cache_stream_url(video_id, audio_url)
            
            self.logger.info(f"✅ Retrieved stream URL for: {video_id}")
            return {**metadata, "streamUrl": audio_url, "stream_url": audio_url, "from_cache": False}
        
        except (CircuitBreakerError, RateLimitError, ExternalServiceError, ValidationError):
            raise
        
        except Exception as e:
            error_message = str(e)
            is_rate_limit = any(keyword in error_message.lower() for keyword in [
                'rate-limit', 'rate limit', 'rate-limited', 'too many requests',
                '429', 'resource_exhausted', 'session has been rate-limited'
            ])
            
            if is_rate_limit:
                youtube_stream_circuit.record_failure(error_message)
                status = youtube_stream_circuit.get_status()
                self.logger.error(f"Rate limit hit for stream: {video_id}")
                raise RateLimitError(
                    message="Límite de peticiones excedido. Intenta más tarde.",
                    details={
                        "operation": "get_stream_url",
                        "retry_after": status['remaining_time_seconds']
                    }
                )
            
            self.logger.error(f"Error getting stream for {video_id}: {error_message}")
            raise ExternalServiceError(
                message="Error obteniendo stream de audio. Intenta más tarde.",
                details={"operation": "get_stream_url", "video_id": video_id}
            )
    
    def _get_best_thumbnail(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract the best quality thumbnail from an item."""
        thumbnails = item.get('thumbnails', [])
        
        # Get the largest thumbnail from the list
        if thumbnails and isinstance(thumbnails, list):
            sorted_thumbs = sorted(
                thumbnails,
                key=lambda x: (x.get('width', 0) * x.get('height', 0)),
                reverse=True
            )
            if sorted_thumbs and sorted_thumbs[0].get('url'):
                url = sorted_thumbs[0]['url']
                # Try to get higher quality by modifying the URL
                return self._enhance_thumbnail_url(url)
        
        # Check direct thumbnail field
        thumbnail = item.get('thumbnail')
        if thumbnail and isinstance(thumbnail, str):
            return self._enhance_thumbnail_url(thumbnail)
        
        # Fallback to first thumbnail if available
        if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
            first_thumb = thumbnails[0]
            if isinstance(first_thumb, dict) and first_thumb.get('url'):
                return self._enhance_thumbnail_url(first_thumb['url'])
            elif isinstance(first_thumb, str):
                return self._enhance_thumbnail_url(first_thumb)
        
        # Fallback: Generate thumbnail from YouTube video ID
        video_id = item.get('videoId') or item.get('video_id')
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        return None
    
    def _enhance_thumbnail_url(self, url: str) -> str:
        """Enhance thumbnail URL to get higher quality image."""
        if not url:
            return url
        
        # For Googleusercontent URLs (most common from ytmusicapi)
        if 'googleusercontent.com' in url:
            # Try to increase the size parameter (wXXX-hXXX)
            # Common sizes: 60, 120, 226, 400, 544, 800, 1200
            # Replace wXXX-hXXX with w800-h800 or higher
            enhanced = re.sub(r'=w\d+-h\d+', '=w800-h800', url)
            self.logger.debug(f"Enhanced Google thumbnail: {url} -> {enhanced}")
            return enhanced
        
        # For i.ytimg.com URLs (YouTube video thumbnails)
        if 'i.ytimg.com' in url:
            # Use maxresdefault for highest quality
            if 'maxresdefault' not in url and 'hqdefault' not in url and 'mqdefault' not in url:
                # Extract video ID and return maxresdefault URL
                video_id_match = re.search(r'/vi/([^/]+)/', url)
                if video_id_match:
                    high_quality_url = f"https://i.ytimg.com/vi/{video_id_match.group(1)}/maxresdefault.jpg"
                    self.logger.debug(f"Enhanced YouTube thumbnail: {url} -> {high_quality_url}")
                    return high_quality_url
        
        return url
    
    async def _enrich_item_with_stream(
        self, 
        item: Dict[str, Any], 
        video_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enrich a single item with stream_url and best thumbnail."""
        if not video_id:
            video_id = item.get('videoId') or item.get('video_id')
        
        enriched = item.copy()
        enriched['thumbnail'] = self._get_best_thumbnail(item)
        
        if video_id:
            try:
                stream_data = await self.get_stream_url(video_id)
                # Fix: buscar streamUrl (camelCase) que es lo que devuelve get_stream_url
                if stream_data.get('streamUrl'):
                    enriched['stream_url'] = stream_data['streamUrl']
                elif stream_data.get('stream_url'):
                    enriched['stream_url'] = stream_data['stream_url']
                if stream_data.get('thumbnail'):
                    enriched['thumbnail'] = stream_data['thumbnail']
            except Exception:
                pass
        
        return enriched
    
    async def enrich_items_with_streams(
        self, 
        items: List[Dict[str, Any]], 
        include_stream_urls: bool = True
    ) -> List[Dict[str, Any]]:
        """Enrich multiple items with stream URLs and best thumbnails in parallel."""
        if not items:
            return []
        
        self.logger.debug(f"Enriching {len(items)} items with streams")
        
        items_with_thumbnails = []
        for item in items:
            enriched = item.copy()
            enriched['thumbnail'] = self._get_best_thumbnail(item)
            items_with_thumbnails.append(enriched)
        
        if not include_stream_urls:
            return items_with_thumbnails
        
        video_ids = [
            item.get('videoId') or item.get('video_id')
            for item in items_with_thumbnails
            if item.get('videoId') or item.get('video_id')
        ]
        
        if not video_ids:
            return items_with_thumbnails
        
        stream_tasks = [self._safe_get_stream_url(vid) for vid in video_ids]
        stream_results = await asyncio.gather(*stream_tasks, return_exceptions=True)
        
        # Fix: buscar streamUrl (camelCase) o stream_url (snake_case)
        video_id_to_stream = {
            video_ids[i]: result.get('streamUrl') or result.get('stream_url')
            for i, result in enumerate(stream_results)
            if isinstance(result, dict) and (result.get('streamUrl') or result.get('stream_url'))
        }
        
        enriched_items = []
        for item in items_with_thumbnails:
            enriched_item = item.copy()
            video_id = enriched_item.get('videoId') or enriched_item.get('video_id')
            
            if video_id and video_id in video_id_to_stream:
                enriched_item['stream_url'] = video_id_to_stream[video_id]
            
            if 'thumbnail' not in enriched_item or enriched_item['thumbnail'] is None:
                enriched_item['thumbnail'] = self._get_best_thumbnail(item)
            
            enriched_items.append(enriched_item)
        
        self.logger.info(f"Enriched {len(enriched_items)} items, {len(video_id_to_stream)} with stream URLs")
        return enriched_items
    
    async def _safe_get_stream_url(self, video_id: str) -> Dict[str, Any]:
        """Safely get stream URL, returning empty dict on error."""
        try:
            return await self.get_stream_url(video_id)
        except Exception:
            return {}
    
    async def is_cached(self, video_id: str) -> bool:
        """
        Check if stream URL is cached for a video.
        
        Args:
            video_id: Video ID to check.
            
        Returns:
            True if cached, False otherwise.
        """
        cache_key = self._get_stream_url_cache_key(video_id)
        
        try:
            if await has_cached_key(cache_key):
                # Also check if not expired
                timestamp = await get_cached_timestamp(cache_key)
                if timestamp > 0:
                    elapsed = time.time() - timestamp
                    return elapsed < self.STREAM_URL_TTL
        except Exception:
            pass
        
        return False
    
    async def get_cache_ttl(self, video_id: str) -> int:
        """
        Get remaining TTL for cached stream URL.
        
        Args:
            video_id: Video ID to check.
            
        Returns:
            Seconds remaining in cache, or 0 if not cached.
        """
        cache_key = self._get_stream_url_cache_key(video_id)
        
        try:
            timestamp = await get_cached_timestamp(cache_key)
            if timestamp > 0:
                remaining = int(self.STREAM_URL_TTL - (time.time() - timestamp))
                return max(0, remaining)
        except Exception:
            pass
        
        return 0
