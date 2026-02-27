"""Redis-based caching utilities for API responses."""
import redis.asyncio as redis
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import json
import time
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client, _redis_pool
    
    if _redis_client is None:
        redis_host = settings.REDIS_HOST or 'localhost'
        redis_port = settings.REDIS_PORT or 6379  # Standard Redis port
        
        logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
        
        _redis_pool = redis.ConnectionPool(
            host=redis_host,
            port=redis_port,
            db=settings.REDIS_DB or 0,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            max_connections=10,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        try:
            await _redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
    
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client, _redis_pool
    
    if _redis_client:
        await _redis_client.close()
    if _redis_pool:
        await _redis_pool.disconnect()
    
    _redis_client = None
    _redis_pool = None


def get_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


async def get_cached_value(key: str) -> Optional[Any]:
    """Get a cached value by key from Redis."""
    if not settings.CACHE_ENABLED:
        return None
    
    try:
        client = await get_redis_client()
        value = await client.get(key)
        if value:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(value)
        logger.debug(f"Cache MISS: {key}")
    except Exception as e:
        logger.warning(f"Error getting cached value for {key}: {e}")
    return None


async def set_cached_value(key: str, value: Any, ttl: int = 3600) -> None:
    """
    Set a cached value in Redis with TTL.
    
    Also stores a timestamp key for TTL checking.
    """
    if not settings.CACHE_ENABLED:
        return
    
    try:
        client = await get_redis_client()
        
        # Store the value with TTL
        await client.set(key, json.dumps(value), ex=ttl)
        
        # Store timestamp for this key (same TTL)
        # This allows us to check when the value was cached
        timestamp_key = f"{key}:timestamp"
        current_time = time.time()
        await client.set(timestamp_key, str(current_time), ex=ttl)
        
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.warning(f"Error setting cached value for {key}: {e}")


async def get_cached_timestamp(key: str) -> float:
    """
    Get the timestamp when a cached value was set.
    
    Returns:
        Unix timestamp when the value was cached, or 0 if not found.
    """
    try:
        client = await get_redis_client()
        timestamp_key = f"{key}:timestamp"
        timestamp = await client.get(timestamp_key)
        if timestamp:
            return float(timestamp)
    except Exception as e:
        logger.warning(f"Error getting timestamp for {key}: {e}")
    return 0


async def get_cached_ttl(key: str) -> int:
    """
    Get remaining TTL for a cached key.
    
    Returns:
        Seconds remaining, or -1 if key doesn't exist, -2 if no expiry.
    """
    try:
        client = await get_redis_client()
        ttl = await client.ttl(key)
        return ttl
    except Exception as e:
        logger.warning(f"Error getting TTL for {key}: {e}")
    return -1


async def has_cached_key(key: str) -> bool:
    """Check if a key exists in cache."""
    if not settings.CACHE_ENABLED:
        return False
    
    try:
        client = await get_redis_client()
        exists = await client.exists(key) > 0
        return exists
    except Exception as e:
        logger.warning(f"Error checking cache key {key}: {e}")
    return False


async def delete_cached_key(key: str) -> bool:
    """Delete a key from cache."""
    try:
        client = await get_redis_client()
        # Delete both the key and its timestamp
        await client.delete(key, f"{key}:timestamp")
        return True
    except Exception as e:
        logger.warning(f"Error deleting cache key {key}: {e}")
    return False


async def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries matching pattern."""
    try:
        client = await get_redis_client()
        if pattern:
            keys = []
            async for key in client.scan_iter(match=f"*{pattern}*"):
                keys.append(key)
            if keys:
                await client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys matching {pattern}")
        else:
            await client.flushdb()
            logger.info("Cleared all cache")
    except Exception as e:
        logger.warning(f"Error clearing cache: {e}")


async def get_cache_stats() -> dict:
    """Get cache statistics."""
    try:
        client = await get_redis_client()
        info = await client.info('memory')
        db_size = await client.dbsize()
        return {
            "enabled": settings.CACHE_ENABLED,
            "backend": "redis",
            "used_memory": info.get('used_memory_human', 'N/A'),
            "keys_count": db_size,
            "connected": True,
        }
    except Exception as e:
        logger.warning(f"Error getting cache stats: {e}")
        return {
            "enabled": settings.CACHE_ENABLED,
            "backend": "redis",
            "connected": False,
            "error": str(e),
        }


# Decorator for caching async functions
def cache_result(ttl: Optional[int] = None):
    """
    Decorator to cache async function results in Redis.
    
    Args:
        ttl: Time to live in seconds (defaults to settings.CACHE_TTL)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"music:{func.__name__}:{get_cache_key(*args, **kwargs)}"
            cache_ttl = ttl or settings.CACHE_TTL
            
            # Check Redis cache
            cached = await get_cached_value(cache_key)
            if cached is not None:
                return cached
            
            # Execute function and cache result
            try:
                result = await func(*args, **kwargs)
            except Exception:
                # Don't cache errors
                raise
            
            # Store in Redis
            await set_cached_value(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator


# Alias for backward compatibility
cache_module = {
    'get_cached_value': get_cached_value,
    'set_cached_value': set_cached_value,
    'get_cached_timestamp': get_cached_timestamp,
    'has_cached_key': has_cached_key,
    'clear_cache': clear_cache,
    'get_cache_stats': get_cache_stats,
}
