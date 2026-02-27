"""Unit tests for cache module."""
import pytest
import time
from unittest.mock import patch, MagicMock

from app.core import cache
from app.core.cache import (
    get_cache_key,
    cache_result,
    clear_cache,
    get_cache_stats,
    get_cached_value,
    set_cached_value,
    get_cached_timestamp,
    has_cached_key,
)


class TestGetCacheKey:
    """Test cases for get_cache_key function."""

    def test_get_cache_key_consistent(self):
        """Test get_cache_key returns consistent hash for same input."""
        key1 = get_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = get_cache_key("arg1", "arg2", kwarg1="value1")
        
        assert key1 == key2

    def test_get_cache_key_different_args(self):
        """Test get_cache_key returns different hash for different args."""
        key1 = get_cache_key("arg1")
        key2 = get_cache_key("arg2")
        
        assert key1 != key2

    def test_get_cache_key_different_kwargs(self):
        """Test get_cache_key returns different hash for different kwargs."""
        key1 = get_cache_key(kwarg1="value1")
        key2 = get_cache_key(kwarg1="value2")
        
        assert key1 != key2

    def test_get_cache_key_kwargs_order_independent(self):
        """Test get_cache_key is independent of kwargs order."""
        key1 = get_cache_key(a=1, b=2)
        key2 = get_cache_key(b=2, a=1)
        
        assert key1 == key2

    def test_get_cache_key_returns_string(self):
        """Test get_cache_key returns a string."""
        key = get_cache_key("test")
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length


class TestCacheResult:
    """Test cases for cache_result decorator."""

    @pytest.mark.asyncio
    async def test_cache_result_caches_value(self):
        """Test cache_result caches the function result."""
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func(arg):
            nonlocal call_count
            call_count += 1
            return f"result_{arg}"
        
        # First call
        result1 = await test_func("test")
        assert result1 == "result_test"
        assert call_count == 1
        
        # Second call should return cached value
        result2 = await test_func("test")
        assert result2 == "result_test"
        assert call_count == 1  # Function not called again

    @pytest.mark.asyncio
    async def test_cache_result_different_args(self):
        """Test cache_result caches different values for different args."""
        @cache_result(ttl=60)
        async def test_func(arg):
            return f"result_{arg}"
        
        result1 = await test_func("arg1")
        result2 = await test_func("arg2")
        
        assert result1 == "result_arg1"
        assert result2 == "result_arg2"

    @pytest.mark.asyncio
    async def test_cache_result_expires(self):
        """Test cache_result expires after TTL."""
        call_count = 0
        
        @cache_result(ttl=1)  # 1 second TTL
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        await test_func()
        # Wait for expiration
        time.sleep(1.1)
        await test_func()
        
        # Both calls should execute the function
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_result_does_not_cache_errors(self):
        """Test cache_result does not cache exceptions."""
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        # First call
        with pytest.raises(ValueError):
            await test_func()
        
        assert call_count == 1
        
        # Second call should execute again (not cached)
        with pytest.raises(ValueError):
            await test_func()
        
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_result_disabled(self):
        """Test cache_result when cache is disabled."""
        call_count = 0
        
        @cache_result(ttl=60)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        # Patch settings to disable cache
        with patch.object(cache.settings, 'CACHE_ENABLED', False):
            await test_func()
            await test_func()
        
        # Both calls should execute (cache disabled)
        assert call_count == 2


class TestClearCache:
    """Test cases for clear_cache function."""

    def test_clear_cache_all(self):
        """Test clear_cache clears all entries."""
        # Add some entries
        cache._cache["key1"] = "value1"
        cache._cache["key2"] = "value2"
        cache._cache_timestamps["key1"] = time.time()
        cache._cache_timestamps["key2"] = time.time()
        
        clear_cache()
        
        assert len(cache._cache) == 0
        assert len(cache._cache_timestamps) == 0

    def test_clear_cache_with_pattern(self):
        """Test clear_cache clears entries matching pattern."""
        cache._cache["search:abc"] = "value1"
        cache._cache["search:def"] = "value2"
        cache._cache["browse:xyz"] = "value3"
        cache._cache_timestamps["search:abc"] = time.time()
        cache._cache_timestamps["search:def"] = time.time()
        cache._cache_timestamps["browse:xyz"] = time.time()
        
        clear_cache("search")
        
        assert "search:abc" not in cache._cache
        assert "search:def" not in cache._cache
        assert "browse:xyz" in cache._cache


class TestGetCacheStats:
    """Test cases for get_cache_stats function."""

    def test_get_cache_stats_empty(self):
        """Test get_cache_stats with empty cache."""
        clear_cache()
        
        stats = get_cache_stats()
        
        assert stats["size"] == 0
        assert "max_size" in stats
        assert "ttl" in stats

    def test_get_cache_stats_with_entries(self):
        """Test get_cache_stats with cached entries."""
        clear_cache()
        cache._cache["key1"] = "value1"
        cache._cache["key2"] = "value2"
        
        stats = get_cache_stats()
        
        assert stats["size"] == 2


class TestCacheHelpers:
    """Test cases for cache helper functions."""

    def test_get_cached_value(self):
        """Test get_cached_value retrieves value."""
        cache._cache["test_key"] = "test_value"
        
        result = get_cached_value("test_key")
        
        assert result == "test_value"

    def test_get_cached_value_not_found(self):
        """Test get_cached_value returns None for missing key."""
        result = get_cached_value("nonexistent_key")
        
        assert result is None

    def test_set_cached_value(self):
        """Test set_cached_value stores value."""
        set_cached_value("new_key", "new_value")
        
        assert cache._cache["new_key"] == "new_value"
        assert "new_key" in cache._cache_timestamps

    def test_get_cached_timestamp(self):
        """Test get_cached_timestamp returns timestamp."""
        set_cached_value("timestamp_key", "value")
        
        result = get_cached_timestamp("timestamp_key")
        
        assert result > 0

    def test_get_cached_timestamp_not_found(self):
        """Test get_cached_timestamp returns 0 for missing key."""
        result = get_cached_timestamp("nonexistent")
        
        assert result == 0

    def test_has_cached_key_true(self):
        """Test has_cached_key returns True for existing key."""
        cache._cache["existing_key"] = "value"
        
        assert has_cached_key("existing_key") is True

    def test_has_cached_key_false(self):
        """Test has_cached_key returns False for missing key."""
        assert has_cached_key("nonexistent_key") is False


class TestCacheMaxSize:
    """Test cases for cache max size behavior."""

    @pytest.mark.asyncio
    async def test_cache_respects_max_size(self):
        """Test cache removes oldest entry when max size is reached."""
        # Set a small max size
        with patch.object(cache.settings, 'CACHE_MAX_SIZE', 2):
            call_count = {"a": 0, "b": 0, "c": 0}
            
            @cache_result(ttl=60)
            async def test_func(key):
                call_count[key] += 1
                return f"result_{key}"
            
            # Fill cache
            await test_func("a")
            await test_func("b")
            
            # Add one more (should evict oldest)
            await test_func("c")
            
            # "a" should have been evicted, so calling it again should re-execute
            await test_func("a")
            
            # "a" was called twice (evicted and recalled)
            assert call_count["a"] == 2
