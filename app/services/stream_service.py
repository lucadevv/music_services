"""Service for streaming audio."""
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import asyncio
import yt_dlp
from app.core.config import get_settings
from app.core.cache import _cache, _cache_timestamps
from app.core.circuit_breaker import youtube_stream_circuit


class StreamService:
    """Service for audio streaming with intelligent caching."""
    
    METADATA_TTL = 86400  # 1 día - metadatos no cambian
    STREAM_URL_TTL = 14400  # 4 horas - URLs expiran
    
    def __init__(self):
        self.settings = get_settings()
    
    def _get_metadata_cache_key(self, video_id: str) -> str:
        """Cache key for metadata (long TTL)."""
        return f"stream_metadata:{video_id}"
    
    def _get_stream_url_cache_key(self, video_id: str) -> str:
        """Cache key for stream URL (short TTL)."""
        return f"stream_url:{video_id}"
    
    def _get_cached_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata if available and not expired."""
        if not self.settings.CACHE_ENABLED:
            return None
        
        cache_key = self._get_metadata_cache_key(video_id)
        if cache_key not in _cache:
            return None
        
        timestamp = _cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp < self.METADATA_TTL:
            return _cache[cache_key]
        
        return None
    
    def _get_cached_stream_url(self, video_id: str) -> Optional[str]:
        """Get cached stream URL if available and not expired."""
        if not self.settings.CACHE_ENABLED:
            return None
        
        cache_key = self._get_stream_url_cache_key(video_id)
        if cache_key not in _cache:
            return None
        
        timestamp = _cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp < self.STREAM_URL_TTL:
            return _cache[cache_key]
        
        return None
    
    def _cache_metadata(self, video_id: str, metadata: Dict[str, Any]):
        """Cache metadata with long TTL."""
        if not self.settings.CACHE_ENABLED:
            return
        
        cache_key = self._get_metadata_cache_key(video_id)
        _cache[cache_key] = metadata
        _cache_timestamps[cache_key] = time.time()
    
    def _cache_stream_url(self, video_id: str, stream_url: str):
        """Cache stream URL with short TTL."""
        if not self.settings.CACHE_ENABLED:
            return
        
        cache_key = self._get_stream_url_cache_key(video_id)
        _cache[cache_key] = stream_url
        _cache_timestamps[cache_key] = time.time()
    
    async def get_stream_url(self, video_id: str) -> Dict[str, Any]:
        """
        Get audio stream URL with intelligent caching.
        
        Strategy:
        1. Check cached metadata (1 day TTL)
        2. Check cached stream URL (4 hours TTL)
        3. If both cached and valid, return immediately (0 YouTube calls)
        4. If metadata cached but stream expired, refresh only stream URL
        5. If nothing cached, fetch everything from YouTube
        """
        if youtube_stream_circuit.is_open():
            status = youtube_stream_circuit.get_status()
            raise Exception(
                f"YouTube API está rate-limited. "
                f"Espera {status['remaining_time_seconds']} segundos. "
                f"Estado: {status['state']}"
            )
        
        cached_metadata = self._get_cached_metadata(video_id)
        cached_stream_url = self._get_cached_stream_url(video_id)
        
        if cached_metadata and cached_stream_url:
            return {**cached_metadata, "url": cached_stream_url}
        
        try:
            url = f"https://music.youtube.com/watch?v={video_id}"
            # yt-dlp no necesita autenticación para extraer streams públicos
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio/best'
            }
            
            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await asyncio.to_thread(extract_info)
            
            audio_url = None
            for f in info.get('adaptive_formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_url = f['url']
                    break
            
            if not audio_url:
                for f in info.get('formats', []):
                    if f.get('acodec') != 'none':
                        audio_url = f['url']
                        break
            
            if not audio_url:
                return {"detail": "yt-dlp no pudo obtener el stream. Verifica el ID o tus cookies."}
            
            youtube_stream_circuit.record_success()
            
            metadata = {
                "title": info.get('title'),
                "artist": info.get('artist', info.get('uploader')),
                "duration": info.get('duration'),
                "thumbnail": info.get('thumbnail')
            }
            
            self._cache_metadata(video_id, metadata)
            self._cache_stream_url(video_id, audio_url)
            
            return {**metadata, "url": audio_url}
        
        except Exception as e:
            error_message = str(e)
            is_rate_limit = any(keyword in error_message.lower() for keyword in [
                'rate-limit', 'rate limit', 'rate-limited', 'too many requests',
                '429', 'resource_exhausted', 'session has been rate-limited'
            ])
            
            if is_rate_limit:
                youtube_stream_circuit.record_failure(error_message)
                status = youtube_stream_circuit.get_status()
                raise Exception(
                    f"YouTube API rate-limited: {error_message}. "
                    f"Circuit breaker activado. Espera {status['remaining_time_seconds']} segundos."
                )
            
            raise Exception(f"Error obteniendo stream: {error_message}")
    
    def _get_best_thumbnail(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract the best quality thumbnail from an item."""
        thumbnails = item.get('thumbnails', [])
        if thumbnails and isinstance(thumbnails, list):
            sorted_thumbs = sorted(
                thumbnails,
                key=lambda x: (x.get('width', 0) * x.get('height', 0)),
                reverse=True
            )
            if sorted_thumbs and sorted_thumbs[0].get('url'):
                return sorted_thumbs[0]['url']
        
        thumbnail = item.get('thumbnail')
        if thumbnail and isinstance(thumbnail, str):
            return thumbnail
        
        if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
            first_thumb = thumbnails[0]
            if isinstance(first_thumb, dict) and first_thumb.get('url'):
                return first_thumb['url']
            elif isinstance(first_thumb, str):
                return first_thumb
        
        return None
    
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
                if stream_data.get('url'):
                    enriched['stream_url'] = stream_data['url']
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
        
        video_id_to_stream = {
            video_ids[i]: result['url']
            for i, result in enumerate(stream_results)
            if isinstance(result, dict) and result.get('url')
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
        
        return enriched_items
    
    async def _safe_get_stream_url(self, video_id: str) -> Dict[str, Any]:
        """Safely get stream URL, returning empty dict on error."""
        try:
            return await self.get_stream_url(video_id)
        except Exception:
            return {}