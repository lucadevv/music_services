"""Caching utilities for API responses."""
from typing import Optional, Any
from functools import wraps
import hashlib
import json
import time
from app.core.config import get_settings

settings = get_settings()

# Simple in-memory cache
_cache: dict = {}
_cache_timestamps: dict = {}


def get_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_result(ttl: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (defaults to settings.CACHE_TTL)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{func.__name__}:{get_cache_key(*args, **kwargs)}"
            
            # Check cache
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, 0)
                cache_ttl = ttl or settings.CACHE_TTL
                
                if time.time() - timestamp < cache_ttl:
                    return _cache[cache_key]
                else:
                    # Expired, remove from cache
                    _cache.pop(cache_key, None)
                    _cache_timestamps.pop(cache_key, None)
            
            # Execute function and cache result
            try:
                result = await func(*args, **kwargs)
            except Exception:
                # Don't cache errors, propagate them
                raise
            
            # Store in cache (respect max size)
            if len(_cache) >= settings.CACHE_MAX_SIZE:
                # Remove oldest entry (simple FIFO)
                oldest_key = min(_cache_timestamps.items(), key=lambda x: x[1])[0]
                _cache.pop(oldest_key, None)
                _cache_timestamps.pop(oldest_key, None)
            
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()
            
            return result
        
        return wrapper
    return decorator


def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries matching pattern."""
    if pattern:
        keys_to_remove = [k for k in _cache.keys() if pattern in k]
        for key in keys_to_remove:
            _cache.pop(key, None)
            _cache_timestamps.pop(key, None)
    else:
        _cache.clear()
        _cache_timestamps.clear()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    return {
        "enabled": settings.CACHE_ENABLED,
        "size": len(_cache),
        "max_size": settings.CACHE_MAX_SIZE,
        "ttl": settings.CACHE_TTL
    }
