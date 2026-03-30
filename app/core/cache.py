"""Caching utilities for API responses - Redis backend."""
from app.core.cache_redis import (
    get_redis_client,
    get_cache_key,
    get_cached_value,
    set_cached_value,
    get_cached_timestamp,
    get_cached_ttl,
    has_cached_key,
    delete_cached_key,
    clear_cache,
    get_cache_stats,
    cache_result,
    settings,
)

__all__ = [
    "get_redis_client",
    "get_cache_key",
    "get_cached_value",
    "set_cached_value",
    "get_cached_timestamp",
    "get_cached_ttl",
    "has_cached_key",
    "delete_cached_key",
    "clear_cache",
    "get_cache_stats",
    "cache_result",
    "settings",
]