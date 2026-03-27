"""Runtime Stream URL Enrichment.

Injects fresh stream URLs into cached metadata responses.
Stream URLs are never embedded in endpoint/metadata cache — only injected at runtime
from the dedicated stream URL cache (music:stream:url:{video_id}).

This guarantees clients always receive valid, non-expired stream URLs.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from app.core.cache_redis import get_cached_value
from app.services.stream_service import StreamService

logger = logging.getLogger(__name__)

# How many concurrent stream URL fetches for uncached items
MAX_CONCURRENT_FETCHES = 10


def _extract_video_ids(data: Any, ids: Optional[Set[str]] = None) -> Set[str]:
    """Recursively extract all videoId/video_id fields from a response."""
    if ids is None:
        ids = set()

    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("videoId", "video_id") and isinstance(value, str) and value:
                ids.add(value)
            elif isinstance(value, (dict, list)):
                _extract_video_ids(value, ids)
    elif isinstance(data, list):
        for item in data:
            _extract_video_ids(item, ids)

    return ids


def _inject_stream_url_into_item(item: Dict[str, Any], stream_urls: Dict[str, str]) -> Dict[str, Any]:
    """Inject streamUrl into a single item that has a videoId."""
    if not isinstance(item, dict):
        return item

    video_id = item.get("videoId") or item.get("video_id")
    if video_id and video_id in stream_urls:
        item["streamUrl"] = stream_urls[video_id]

    # Recurse into nested dicts/lists
    for key, value in item.items():
        if isinstance(value, dict):
            _inject_stream_url_into_item(value, stream_urls)
        elif isinstance(value, list):
            for sub_item in value:
                if isinstance(sub_item, dict):
                    _inject_stream_url_into_item(sub_item, stream_urls)

    return item


async def enrich_with_fresh_streams(
    data: Dict[str, Any],
    stream_service: Optional[StreamService] = None,
) -> Dict[str, Any]:
    """
    Inject fresh stream URLs into a metadata response.

    Flow:
    1. Extract all videoIds from the response
    2. Batch MGET from stream cache (music:stream:url:{video_id})
    3. For uncached videoIds, fetch fresh URLs via stream service (parallel)
    4. Inject streamUrl into each item
    5. Return enriched response (original data is NOT modified in cache)

    This is the ONLY way stream URLs should be added to responses.
    """
    if stream_service is None:
        stream_service = StreamService()

    # 1. Extract video IDs
    video_ids = _extract_video_ids(data)
    if not video_ids:
        return data

    # 2. Batch check stream cache
    cached_urls = {}
    uncached_ids = []

    for vid in video_ids:
        cache_key = f"music:stream:url:{vid}"
        cached_url = await get_cached_value(cache_key)
        if cached_url:
            cached_urls[vid] = cached_url
        else:
            uncached_ids.append(vid)

    # 3. Fetch uncached in parallel (with concurrency limit)
    if uncached_ids:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)

        async def _fetch_one(vid: str) -> tuple:
            async with semaphore:
                try:
                    result = await stream_service.get_stream_url(vid, bypass_cache=False)
                    url = result.get("streamUrl")
                    if url:
                        return (vid, url)
                except Exception as e:
                    logger.debug(f"Could not fetch stream URL for {vid}: {e}")
                return (vid, None)

        tasks = [_fetch_one(vid) for vid in uncached_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, tuple):
                vid, url = result
                if url:
                    cached_urls[vid] = url

    # 4. Inject into response
    if cached_urls:
        _inject_stream_url_into_item(data, cached_urls)

    logger.info(f"Enriched {len(cached_urls)}/{len(video_ids)} stream URLs at runtime")
    return data


async def get_fresh_stream_url(video_id: str, stream_service: Optional[StreamService] = None) -> Optional[str]:
    """
    Get a guaranteed-fresh stream URL for a single video.

    1. Check cache first
    2. If not cached, fetch fresh
    3. Return URL or None
    """
    if stream_service is None:
        stream_service = StreamService()

    try:
        # Try cache first
        cache_key = f"music:stream:url:{video_id}"
        cached_url = await get_cached_value(cache_key)
        if cached_url:
            return cached_url

        # Fetch fresh
        result = await stream_service.get_stream_url(video_id, bypass_cache=True)
        return result.get("streamUrl")
    except Exception as e:
        logger.error(f"Failed to get fresh stream URL for {video_id}: {e}")
        return None
