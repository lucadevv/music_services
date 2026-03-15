"""Unit tests for cache module (Redis backend)."""
import pytest
import asyncio

from app.core.cache import (
    get_cache_key,
    cache_result,
    get_cache_stats,
    get_cached_value,
    set_cached_value,
    get_cached_timestamp,
    has_cached_key,
)
from app.core.cache_redis import get_redis_client, clear_cache as redis_clear_cache


class TestGetCacheKey:
    def test_get_cache_key_consistent(self):
        key1 = get_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = get_cache_key("arg1", "arg2", kwarg1="value1")
        
        assert key1 == key2

    def test_get_cache_key_different_args(self):
        key1 = get_cache_key("arg1")
        key2 = get_cache_key("arg2")
        
        assert key1 != key2

    def test_get_cache_key_different_kwargs(self):
        key1 = get_cache_key(kwarg1="value1")
        key2 = get_cache_key(kwarg1="value2")
        
        assert key1 != key2

    def test_get_cache_key_kwargs_order_independent(self):
        key1 = get_cache_key(a=1, b=2)
        key2 = get_cache_key(b=2, a=1)
        
        assert key1 == key2

    def test_get_cache_key_returns_string(self):
        key = get_cache_key("test")
        
        assert isinstance(key, str)
        assert len(key) == 32


@pytest.mark.asyncio
class TestCacheResult:
    async def test_cache_result_caches_value(self):
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        result1 = await test_func("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        result2 = await test_func("test")
        assert result2 == "result_test"
        assert call_count == 1

    async def test_cache_result_different_args(self):
        @cache_result(ttl=60)
        async def test_func(arg):
            return f"result_{arg}"
        
        result1 = await test_func("arg1")
        result2 = await test_func("arg2")
        
        assert result1 == "result_arg1"
        assert result2 == "result_arg2"

    async def test_cache_result_expires(self):
        call_count = 0
        
        @cache_result(ttl=1)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        await test_func()
        await asyncio.sleep(1.1)
        await test_func()
        
        assert call_count == 2

    async def test_cache_result_does_not_cache_errors(self):
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await test_func()
        
        assert call_count == 1
        
        with pytest.raises(ValueError):
            await test_func()
        
        assert call_count == 2

    async def test_cache_result_disabled(self):
        from app.core import cache
        
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        original_enabled = cache.settings.CACHE_ENABLED
        cache.settings.CACHE_ENABLED = False
        
        try:
            await test_func()
            await test_func()
            assert call_count == 2
        finally:
            cache.settings.CACHE_ENABLED = original_enabled


@pytest.mark.asyncio
class TestClearCache:
    async def test_clear_cache_all(self):
        client = await get_redis_client()
        await client.set("test:key1", "value1")
        await client.set("test:key2", "value2")
        
        await redis_clear_cache()
        
        assert await client.get("test:key1") is None
        assert await client.get("test:key2") is None

    async def test_clear_cache_with_pattern(self):
        client = await get_redis_client()
        
        await client.set("search:abc", "value1")
        await client.set("search:def", "value2")
        await client.set("browse:xyz", "value3")
        
        await redis_clear_cache("search")
        
        assert await client.get("search:abc") is None
        assert await client.get("search:def") is None
        assert await client.get("browse:xyz") == "value3"


@pytest.mark.asyncio
class TestGetCacheStats:
    async def test_get_cache_stats_empty(self):
        client = await get_redis_client()
        await client.flushdb()
        
        stats = await get_cache_stats()
        
        assert stats["enabled"] == True
        assert stats["backend"] == "redis"

    async def test_get_cache_stats_with_entries(self):
        client = await get_redis_client()
        await client.set("test:key1", "value1")
        
        stats = await get_cache_stats()
        
        assert stats["enabled"] == True
        assert stats["backend"] == "redis"


@pytest.mark.asyncio
class TestCacheHelpers:
    async def test_get_cached_value(self):
        client = await get_redis_client()
        await client.set("test_key", '"test_value"')
        
        result = await get_cached_value("test_key")
        
        assert result == "test_value"

    async def test_get_cached_value_not_found(self):
        result = await get_cached_value("nonexistent_key")
        
        assert result is None

    async def test_set_cached_value(self):
        client = await get_redis_client()
        
        await set_cached_value("new_key", "new_value", ttl=60)
        
        result = await client.get("new_key")
        
        assert result == '"new_value"'

    async def test_get_cached_timestamp(self):
        client = await get_redis_client()
        
        await set_cached_value("timestamp_key", "value", ttl=60)
        
        result = await get_cached_timestamp("timestamp_key")
        
        assert result > 0

    async def test_get_cached_timestamp_not_found(self):
        result = await get_cached_timestamp("nonexistent")
        
        assert result == 0

    async def test_has_cached_key_true(self):
        client = await get_redis_client()
        await client.set("existing_key", "value")
        
        result = await has_cached_key("existing_key")
        
        assert result is True

    async def test_has_cached_key_false(self):
        result = await has_cached_key("nonexistent_key")
        
        assert result is False


@pytest.mark.asyncio
class TestCacheMaxSize:
    async def test_cache_works_with_redis(self):
        call_count = {"a": 0, "b": 0}
        
        @cache_result(ttl=60)
        async def test_func(key):
            call_count[key] += 1
            return f"result_{key}"
        
        await test_func("a")
        await test_func("b")
        
        assert call_count["a"] == 1
        assert call_count["b"] == 1
        
        await test_func("a")
        assert call_count["a"] == 1