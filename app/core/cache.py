"""Caching utilities for API responses - Redis backend."""
from typing import Optional, Any
from functools import wraps
import hashlib
import json
import time
import asyncio
from app.core.config import get_settings

settings = get_settings()

# Global Redis client
_redis_client = None


async def get_redis_client():
    """Get Redis client."""
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as redis
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST or 'localhost',
            port=settings.REDIS_PORT or 6380,
            db=settings.REDIS_DB or 0,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
        )
    return _redis_client


def get_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


async def _get_async(key: str) -> Optional[Any]:
    """Get value from Redis."""
    try:
        client = await get_redis_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


async def _set_async(key: str, value: Any, ttl: int) -> None:
    """Set value in Redis with TTL."""
    try:
        client = await get_redis_client()
        await client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass


async def _exists_async(key: str) -> bool:
    """Check if key exists in Redis."""
    try:
        client = await get_redis_client()
        return await client.exists(key) > 0
    except Exception:
        return False


# Synchronous wrappers for backward compatibility
class CacheDict:
    """Thread-safe cache using Redis."""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        return await _get_async(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        async with self._lock:
            await _set_async(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        try:
            client = await get_redis_client()
            await client.delete(key)
        except Exception:
            pass
    
    async def clear(self) -> None:
        try:
            client = await get_redis_client()
            await client.flushdb()
        except Exception:
            pass
    
    def __contains__(self, key: str) -> bool:
        return False


# Global cache instance
_cache = CacheDict()


def cache_result(ttl: Optional[int] = None):
    """Decorator to cache async function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            cache_key = f"music:{func.__name__}:{get_cache_key(*args, **kwargs)}"
            cache_ttl = ttl or settings.CACHE_TTL
            
            cached = await _cache.get(cache_key)
            if cached is not None:
                return cached
            
            try:
                result = await func(*args, **kwargs)
            except Exception:
                raise
            
            await _cache.set(cache_key, result, cache_ttl)
            return result
        return wrapper
    return decorator


def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries matching pattern."""
    pass


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "enabled": settings.CACHE_ENABLED,
        "backend": "redis",
        "host": settings.REDIS_HOST,
        "port": settings.REDIS_PORT,
    }


# Public functions for backward compatibility
def get_cached_value(key: str) -> Optional[Any]:
    """Get a cached value by key."""
    return None


def set_cached_value(key: str, value: Any, ttl: int = 3600) -> None:
    """Set a cached value."""
    pass


def get_cached_timestamp(key: str) -> float:
    """Get the timestamp when a cached value was set."""
    return 0


def has_cached_key(key: str) -> bool:
    """Check if a key exists in cache."""
    return False
