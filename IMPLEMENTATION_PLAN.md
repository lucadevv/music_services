# 🎵 IMPLEMENTATION PLAN: API FIXING & INTELLIGENT CACHING INTEGRATION

**Date:** 28 March 2026
**Project:** YouTube Music API Service
**Priority:** CRITICAL

---

## 📊 CURRENT STATE ANALYSIS

### Overview
- **Total Endpoints:** 38
- **Passing:** 9 (23.7%)
- **Failing:** 27 (71.1%)
- **Inconsistencies:** 1 (2.6%)
- **Informational:** 1 (2.6%)

### Key Findings

#### 1. Authentication Issues (5 endpoints)
- **Problem:** Admin key not properly validated
- **Impact:** All OAuth/credentials endpoints return 403 Forbidden
- **Root Cause:** `ADMIN_SECRET_KEY` from `.env` not being read correctly
- **Affected:** `/auth/*` endpoints (lines 2-6 in test report)

#### 2. Browse/Explore/Playlists (15 endpoints)
- **Problem:** YouTube Music API returns `EXTERNAL_SERVICE_ERROR`
- **Impact:** All browse, explore, and playlist endpoints fail
- **Root Cause:** Missing OAuth authentication to YouTube Music
- **Affected:**
  - Browse: 7 endpoints (lines 7-14, 28)
  - Explore: 5 endpoints (lines 15-19, 41)
  - Playlists: 1 endpoint (line 23)
  - Watch: 1 endpoint (line 24) - 307 redirect

#### 3. Search (3 endpoints)
- **Problem:** YouTube Music API returns non-JSON responses
- **Impact:** Search and suggestions endpoints fail
- **Root Cause:** YouTube Music API authentication issues
- **Affected:** `/search/*` endpoints (lines 20-22)

#### 4. Podcasts (5 endpoints)
- **Problem:** 404 errors - endpoints not implemented
- **Impact:** Podcast functionality completely broken
- **Root Cause:** Missing implementation
- **Affected:** `/podcasts/*` endpoints (lines 25-29)

#### 5. Stream URLs (8 endpoints)
- **Status:** 5/8 passing, 3/8 failing
- **What Works:** Basic stream URL extraction, batch processing, cache operations
- **What Fails:**
  - `/stream/cache/info/{video_id}` - Internal error
  - `/stream/proxy/{video_id}` - UTF-8 decode error
   - Cache metadata not being retrieved properly
 
#### 6. Statistics
- **Stats:** ✅ Passing (line 37)
 
---

## 🎯 ROOT CAUSES

### Primary Issues

1. **OAuth Configuration Missing**
   - `ytmusicapi` client not properly authenticated
   - Missing OAuth credentials in Google Cloud Console
   - YouTube Music API quota exhausted or quota limit reached
   - API key invalid or not configured

2. **Admin Key Authentication Broken**
   - Environment variable not loading correctly
   - Middleware not validating X-Admin-Key header
   - Inconsistent authentication across endpoints

3. **YouTube API Rate Limiting**
   - API quota being exceeded (100k units/day)
   - Missing circuit breaker implementation for YouTube API
   - No retry logic with exponential backoff
   - Missing rate limit headers from YouTube API

4. **Metadata Cache Not Working**
   - Cache keys not matching between reads/writes
   - TTL configuration inconsistent
   - Timestamp tracking not implemented properly
   - Cache invalidation not working

5. **Stream URL Cache Not Optimized**
   - Default TTL too short (1 hour) vs actual YouTube URL lifetime (6-12 hours)
   - No background refresh mechanism
   - Metadata cache not being utilized before fetching stream URLs
   - Batch operations not optimized

---

## 🏗️ ARCHITECTURE SOLUTION

### Core Strategy: Hybrid ytmusicapi + yt-dlp Approach

#### 1. OAuth Integration with ytmusicapi
```python
# app/core/ytmusic_client.py
from ytmusicapi import YTMusic
from ytmusicapi.oauth import OAuthCredentials, OAuthCredentialsJSON

async def get_authenticated_ytmusic():
    """
    Get authenticated YTMusic client with fallback logic.

    Priority:
    1. OAuth credentials from .env
    2. OAuth JSON file
    3. Browser authentication (first run)
    4. Anonymous mode (fallback)
    """
    credentials = await load_credentials()
    try:
        return YTMusic(credentials)
    except Exception as e:
        logger.warning(f"OAuth failed: {e}")
        return YTMusic()  # Fallback to anonymous
```

#### 2. yt-dlp Integration for Streaming
```python
# app/services/stream_service.py
class StreamService:
    def __init__(self):
        self.yt_dlp_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'prefer_ffmpeg': True,
            'restrictfilenames': True,
        }

    async def get_stream_url(self, video_id: str) -> str:
        """
        Get audio stream URL using yt-dlp.
        Returns: Direct URL or error message
        """
        try:
            # Try cached metadata first
            metadata = await self._get_cached_metadata(video_id)
            if metadata:
                return metadata.get('streamUrl', '')

            # Get video info
            info = await self._get_video_info(video_id)

            # Extract stream URL
            stream_url = self._extract_stream_url(info)
            await self._cache_stream_url(video_id, stream_url)

            return stream_url
        except Exception as e:
            return f"ERROR: {str(e)}"
```

#### 3. Redis Caching Strategy

**Metadata Cache (20 hours)**
```python
# Metadata for browse, explore, search results
CACHE_KEYS:
- music:browse:metadata:{browse_id}
- music:search:{query_hash}
- music:explore:{category}
- music:playlist:{playlist_id}

TTL: 72000 seconds (20 hours)
Strategy: Cache-aside pattern with background refresh
```

**Stream URL Cache (5 hours)**
```python
# Stream URLs for direct playback
CACHE_KEYS:
- music:stream:url:{video_id}
- music:stream:metadata:{video_id}

TTL: 18000 seconds (5 hours)
Strategy: Lazy loading with TTL expiration
Background refresh: Check if URL within 1h of expiration and refresh
```

#### 4. Circuit Breaker Implementation
```python
# app/core/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
```

---

## 📝 CODE CHANGES REQUIRED

### Phase 1: OAuth Configuration (CRITICAL)

#### File: `app/core/ytmusic_client.py` (NEW)
```python
"""YTMusic client with OAuth support."""
import json
import asyncio
import logging
from typing import Optional
from pathlib import Path
from ytmusicapi import YTMusic, OAuthCredentials, OAuthCredentialsJSON

logger = logging.getLogger(__name__)


async def load_credentials() -> Optional[OAuthCredentials]:
    """Load OAuth credentials from environment or file."""
    from app.core.config import get_settings
    settings = get_settings()

    # Priority 1: OAuth JSON file
    if settings.OAUTH_JSON_PATH and Path(settings.OAUTH_JSON_PATH).exists():
        try:
            with open(settings.OAUTH_JSON_PATH) as f:
                credentials_data = json.load(f)
            credentials = OAuthCredentialsJSON(credentials_data)
            logger.info("✅ Loaded OAuth credentials from file")
            return credentials
        except Exception as e:
            logger.warning(f"Error loading OAuth JSON: {e}")

    # Priority 2: Client ID/Secret from environment
    if settings.YTMUSIC_CLIENT_ID and settings.YTMUSIC_CLIENT_SECRET:
        try:
            credentials = OAuthCredentials(
                client_id=settings.YTMUSIC_CLIENT_ID,
                client_secret=settings.YTMUSIC_CLIENT_SECRET,
            )
            logger.info("✅ Loaded OAuth credentials from env vars")
            return credentials
        except Exception as e:
            logger.warning(f"Error creating OAuth credentials: {e}")

    return None


async def get_authenticated_ytmusic() -> YTMusic:
    """
    Get authenticated YTMusic client.

    Returns:
        YTMusic client instance (may be anonymous if auth fails)
    """
    credentials = await load_credentials()

    if credentials:
        try:
            ytmusic = YTMusic(credentials)
            # Test the connection
            result = await asyncio.to_thread(ytmusic.get_home)
            if result:
                logger.info("✅ YTMusic OAuth authenticated successfully")
                return ytmusic
            else:
                logger.warning("⚠️  OAuth credentials invalid (empty response)")
        except Exception as e:
            logger.warning(f"⚠️  OAuth authentication failed: {e}")

    # Fallback to anonymous mode
    logger.warning("⚠️  Falling back to anonymous mode (limited functionality)")
    return YTMusic()


async def get_anonymous_ytmusic() -> YTMusic:
    """Get anonymous YTMusic client."""
    return YTMusic()


async def initialize_ytmusic():
    """Initialize YTMusic client with proper authentication."""
    from app.core.config import get_settings
    settings = get_settings()

    if settings.YTMUSIC_CLIENT_ID or settings.OAUTH_JSON_PATH:
        return await get_authenticated_ytmusic()
    return await get_anonymous_ytmusic()
```

#### File: `app/api/v1/endpoints/auth.py` (FIX)
```python
# Add proper admin key validation
from app.core.config import get_settings

@app.post("/api/v1/auth/credentials")
async def save_credentials(request: AuthCredentialsRequest):
    """Save OAuth credentials."""
    # Fix: Read ADMIN_SECRET_KEY from settings
    settings = get_settings()

    # Validate admin key
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=403,
            detail="ADMIN_SECRET_KEY inválida"
        )

    # Save credentials logic...
```

### Phase 2: Browse Service Fixes

#### File: `app/services/browse_service.py` (FIX)
```python
async def get_home(self) -> List[Dict[str, Any]]:
    """Get home page content with retry logic."""
    self._log_operation("get_home")

    # Circuit breaker check
    if youtube_stream_circuit.state == 'OPEN':
        raise CircuitBreakerError("YouTube API circuit breaker is OPEN")

    # Retry with exponential backoff
    async def fetch_home():
        return await asyncio.to_thread(self.ytmusic.get_home)

    last_error = None
    for attempt in range(self.MAX_RETRIES):
        try:
            result = await fetch_home()
            if result and len(result) > 0:
                self.logger.info(f"✅ Retrieved home page: {len(result)} sections")
                await self._cache_result("get_home", result)
                return result

            # Empty response
            if attempt == 0:
                # First attempt with empty result - might be auth issue
                raise ResourceNotFoundError("Empty response from YouTube Music")

        except (ResourceNotFoundError, YTMusicServiceException) as e:
            raise  # Re-raise custom exceptions
        except Exception as e:
            last_error = e
            if attempt < self.MAX_RETRIES - 1:
                wait_time = self.BASE_DELAY * (2 ** attempt)
                await asyncio.sleep(wait_time)
                self.logger.warning(f"Retry {attempt + 1}/{self.MAX_RETRIES} after {wait_time}s")

    # All retries failed
    raise YTMusicServiceException(
        message=f"Failed to get home after {self.MAX_RETRIES} attempts",
        details={"last_error": str(last_error)}
    )
```

### Phase 3: Search Service Improvements

#### File: `app/services/search_service.py` (FIX)
```python
async def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
    """Search with error handling and fallback."""
    self._log_operation("search", query=query)

    # Circuit breaker check
    if youtube_stream_circuit.state == 'OPEN':
        raise CircuitBreakerError("YouTube API circuit breaker is OPEN")

    try:
        # Try authenticated search
        result = await asyncio.to_thread(self.ytmusic.search, query, limit)
        if result and len(result) > 0:
            return result

        # Empty result - might need authentication
        raise ResourceNotFoundError("No results found - try using authenticated search")

    except (ResourceNotFoundError, YTMusicServiceException) as e:
        raise
    except json.JSONDecodeError as e:
        raise ExternalServiceError(
            message="YouTube API returned invalid JSON",
            details={"query": query, "error": str(e)}
        )
    except Exception as e:
        raise ExternalServiceError(
            message=f"Search failed: {str(e)}",
            details={"query": query}
        )
```

### Phase 4: Stream Service Optimization

#### File: `app/services/stream_service.py` (OPTIMIZE)
```python
# Update cache configuration
class StreamService(BaseService):
    METADATA_TTL = 72000  # 20 hours - INCREASED
    STREAM_URL_TTL = 18000  # 5 hours - Optimal for YouTube URLs

    def __init__(self):
        super().__init__()
        self.settings = get_settings()

        # Optimize yt-dlp options
        self.yt_dlp_options = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'prefer_ffmpeg': True,
            'restrictfilenames': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,  # Only single video
            'source_address': '0.0.0.0',  # IPv4 only
        }

    async def get_stream_url(self, video_id: str, bypass_cache: bool = False) -> str:
        """Get stream URL with improved caching strategy."""
        if bypass_cache:
            return await self._fetch_stream_url_direct(video_id)

        # Try cache first
        if not bypass_cache:
            cached_url = await self._get_cached_stream_url(video_id)
            if cached_url:
                return cached_url

            cached_metadata = await self._get_cached_metadata(video_id)
            if cached_metadata:
                return cached_metadata.get('streamUrl', '')

        # Not cached - fetch new URL
        return await self._fetch_stream_url_direct(video_id)

    async def _fetch_stream_url_direct(self, video_id: str) -> str:
        """Fetch stream URL directly using yt-dlp."""
        try:
            # Circuit breaker protection
            if youtube_stream_circuit.state == 'OPEN':
                raise CircuitBreakerError("Circuit breaker OPEN")

            info = await self._get_video_info(video_id)
            stream_url = self._extract_stream_url(info)
            await self._cache_stream_url(video_id, stream_url)

            return stream_url

        except CircuitBreakerError as e:
            raise
        except Exception as e:
            self.logger.error(f"Stream URL fetch error: {e}")
            raise ExternalServiceError(message=f"Failed to get stream URL: {str(e)}")
```

### Phase 5: Background Cache Refresher

#### File: `app/core/background_cache.py` (IMPROVE)
```python
"""Background cache refresher for stream URLs."""
import asyncio
import time
from typing import List

async def refresh_expired_streams():
    """
    Background task to refresh stream URLs that are about to expire.
    Checks active streams every hour and refreshes if within 1h of expiration.
    """
    while True:
        try:
            await asyncio.sleep(3600)  # Check every hour

            # Get active streams
            active_streams = await get_active_streams(
                max_idle_time=86400,  # 24 hours
                limit=50
            )

            if not active_streams:
                continue

            # Get stream status
            streams_to_refresh = []
            for video_id in active_streams:
                status_key = f"music:stream:status:{video_id}"
                ttl_key = f"music:stream:url:{video_id}:ttl"

                current_ttl = await get_cached_ttl(ttl_key)
                if current_ttl < 3600:  # Less than 1 hour
                    streams_to_refresh.append(video_id)

            # Refresh expired streams
            if streams_to_refresh:
                self.logger.info(f"🔄 Refreshing {len(streams_to_refresh)} expired streams")

                for video_id in streams_to_refresh:
                    try:
                        await stream_service.get_stream_url(video_id, bypass_cache=True)
                        self.logger.info(f"✅ Refreshed stream: {video_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to refresh {video_id}: {e}")

        except Exception as e:
            self.logger.error(f"Background cache refresh error: {e}")


async def check_metadata_expiry():
    """Check for expired metadata and refresh if needed."""
    while True:
        try:
            await asyncio.sleep(43200)  # Check every 12 hours

            # Get all metadata cache keys
            pattern = "music:browse:metadata:*"
            keys = await get_keys_by_pattern(pattern)

            if keys:
                # Filter expired keys
                expired_keys = []
                for key in keys:
                    ttl = await get_cached_ttl(key)
                    if ttl < 0:
                        expired_keys.append(key)

                if expired_keys:
                    self.logger.info(f"🔄 Refreshing {len(expired_keys)} expired metadata entries")

                    for key in expired_keys:
                        try:
                            # Extract video_id from key
                            video_id = key.split(":")[-1]
                            await stream_service.get_stream_url(video_id, bypass_cache=True)
                        except Exception as e:
                            self.logger.warning(f"Failed to refresh metadata {key}: {e}")

        except Exception as e:
            self.logger.error(f"Metadata expiry check error: {e}")
```

### Phase 6: API Endpoints Fixes

#### File: `app/api/v1/endpoints/stream.py` (FIX)
```python
# Fix cache info endpoint
@app.get("/stream/cache/info/{video_id}")
async def get_stream_cache_info(video_id: str):
    """Get detailed cache information for a stream."""
    try:
        # Get metadata cache info
        metadata_key = f"music:stream:metadata:{video_id}"
        metadata_ttl = await get_cached_ttl(metadata_key)

        # Get stream URL cache info
        url_key = f"music:stream:url:{video_id}"
        url_ttl = await get_cached_ttl(url_key)

        # Check if both exist
        metadata_exists = await has_cached_key(metadata_key)
        url_exists = await has_cached_key(url_key)

        return {
            "video_id": video_id,
            "metadata": {
                "exists": metadata_exists,
                "ttl": metadata_ttl
            },
            "stream_url": {
                "exists": url_exists,
                "ttl": url_ttl
            },
            "status": "cached" if (metadata_exists and url_exists) else "uncached"
        }
    except Exception as e:
        logger.error(f"Error getting stream cache info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cache info: {str(e)}"
        )
```

#### File: `app/api/v1/endpoints/stream.py` (FIX PROXY)
```python
# Fix proxy endpoint to handle UTF-8 encoding
@app.get("/stream/proxy/{video_id}")
async def stream_proxy(
    video_id: str,
    response: Response
):
    """Proxy audio stream with CORS headers."""
    try:
        # Get stream URL
        stream_url = await stream_service.get_stream_url(video_id)

        if stream_url.startswith("ERROR:"):
            return JSONResponse(
                status_code=400,
                content={"error": stream_url}
            )

        # Proxy the stream
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", stream_url) as response:
                # Copy headers
                for key, value in response.headers.items():
                    response.headers[key] = value

                # Set content type
                response.headers["Content-Type"] = "audio/mpeg"

                # Return stream
                return response

    except httpx.RequestError as e:
        logger.error(f"Proxy error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Proxy error: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Stream proxy error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
```

#### File: `app/api/v1/endpoints/podcasts.py` (IMPLEMENT)
```python
"""Podcast endpoints implementation."""
from fastapi import APIRouter, HTTPException, Header
from app.services.podcast_service import PodcastService

router = APIRouter()
podcast_service = PodcastService()


@app.get("/api/v1/podcasts/channel/{channel_id}")
async def get_podcast_channel(channel_id: str):
    """Get podcast channel information."""
    try:
        result = await podcast_service.get_channel(channel_id)
        if not result:
            raise HTTPException(status_code=404, detail="Channel not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/podcasts/channel/{channel_id}/episodes")
async def get_podcast_episodes(channel_id: str, limit: int = 50):
    """Get podcast episodes for a channel."""
    try:
        result = await podcast_service.get_channel_episodes(channel_id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 7: Endpoint 404 Fix

No upload functionality needed - this is a read-only music service.

---

## 📦 INSTALLATION STEPS

### 1. Setup YouTube Music OAuth Credentials

```bash
# Step 1: Go to Google Cloud Console
# https://console.cloud.google.com/

# Step 2: Create OAuth 2.0 credentials
# 1. Go to "APIs & Services" → "Credentials"
# 2. Click "Create Credentials" → "OAuth client ID"
# 3. Application type: "Web application"
# 4. Authorized redirect URIs:
#    - http://localhost:8000/api/v1/auth/oauth/callback
#    - http://localhost:8000/api/v1/auth/oauth/callback

# Step 3: Get Client ID and Client Secret
# Copy them to .env file:
YTMUSIC_CLIENT_ID="your_client_id.apps.googleusercontent.com"
YTMUSIC_CLIENT_SECRET="your_client_secret"

# Step 4: Create oauth.json file for OAuth flow
python -c "
from ytmusicapi import OAuthCredentials
import json

# This will prompt for browser authentication
credentials = OAuthCredentials(
    client_id='your_client_id.apps.googleusercontent.com',
    client_secret='your_client_secret'
)
print(json.dumps(credentials.to_json()))
" > oauth.json

# Step 5: Verify credentials
python -c "
import json
with open('oauth.json') as f:
    data = json.load(f)
    print('✅ OAuth JSON file created successfully')
    print(f'Client ID: {data.get(\"clientId\", \"N/A\")}')
"
```

### 2. Update Dependencies

```bash
# Install required packages
pip install ytmusicapi==1.0.0
pip install yt-dlp>=2023.10.0
pip install redis>=5.0.0
pip install hiredis>=2.2.3
pip install httpx>=0.25.0
pip install slowapi>=0.1.9

# Or install all from requirements.txt
pip install -r requirements.txt --upgrade
```

### 3. Configure Environment Variables

```bash
# Copy .env.example to .env if not exists
cp .env.example .env

# Edit .env with your configuration:
ADMIN_SECRET_KEY="your_secret_admin_key"
YTMUSIC_CLIENT_ID="your_client_id.apps.googleusercontent.com"
YTMUSIC_CLIENT_SECRET="your_client_secret"
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD=""
CACHE_ENABLED="true"
CACHE_TTL="300"
```

### 4. Setup Redis

```bash
# Start Redis (using Docker)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Or install Redis locally
# macOS: brew install redis
# Linux: apt-get install redis-server

# Verify Redis connection
redis-cli ping
# Should return: PONG
```

### 5. Database Migrations (if any)

```bash
# Check for database migrations
ls -la migrations/ 2>/dev/null || echo "No migrations found"

# Run migrations if needed
alembic upgrade head
```

---

## 🧪 TESTING STRATEGY

### Unit Tests

```python
# tests/test_auth.py
async def test_admin_key_validation():
    """Test admin key authentication."""
    response = client.get(
        "/api/v1/auth/status",
        headers={"X-Admin-Key": "wrong_key"}
    )
    assert response.status_code == 403

    response = client.get(
        "/api/v1/auth/status",
        headers={"X-Admin-Key": get_valid_admin_key()}
    )
    assert response.status_code == 200

# tests/test_oauth.py
async def test_ytmusic_auth():
    """Test YTMusic authentication."""
    from app.core.ytmusic_client import get_authenticated_ytmusic

    client = await get_authenticated_ytmusic()
    assert client is not None
    assert client is not ytmusicapi.OAuthError

# tests/test_stream_cache.py
async def test_stream_url_caching():
    """Test stream URL caching behavior."""
    video_id = "rMbATaj7Il8"

    # First call - should fetch from YouTube
    url1 = await stream_service.get_stream_url(video_id)
    assert url1.startswith("http")

    # Second call - should use cache
    url2 = await stream_service.get_stream_url(video_id)
    assert url1 == url2

    # Third call - should still use cache
    url3 = await stream_service.get_stream_url(video_id)
    assert url1 == url3

    # Test cache info
    cache_info = await get_stream_cache_info(video_id)
    assert cache_info["status"] == "cached"

# tests/test_circuit_breaker.py
async def test_circuit_breaker():
    """Test circuit breaker behavior."""
    from app.core.circuit_breaker import CircuitBreaker

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    # Simulate failures
    for _ in range(3):
        with pytest.raises(CircuitBreakerError):
            await breaker.call(broken_function)

    # Circuit should be OPEN
    assert breaker.state == 'OPEN'

    # Wait for recovery
    await asyncio.sleep(65)
    assert breaker.state == 'HALF_OPEN'

    # Success should close circuit
    result = await breaker.call(success_function)
    assert result == "success"
    assert breaker.state == 'CLOSED'
```

### Integration Tests

```bash
# Run all tests
pytest tests/ -v --cov=app --cov-report=html

# Run specific test suites
pytest tests/test_auth.py -v
pytest tests/test_stream.py -v
pytest tests/test_cache.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

### API Endpoint Tests

```python
# tests/test_endpoints.py
async def test_all_endpoints():
    """Test all 38 endpoints with proper authentication."""
    admin_key = get_valid_admin_key()

    test_cases = [
        # Auth endpoints
        ("/api/v1/auth/status", {"X-Admin-Key": admin_key}),
        ("/api/v1/auth/credentials", {"X-Admin-Key": admin_key}, "POST", {}),

        # Browse endpoints
        ("/api/v1/browse/home", {}),
        ("/api/v1/browse/album/MPREb123456", {}),
        ("/api/v1/browse/song/rMbATaj7Il8", {}),

        # Explore endpoints
        ("/api/v1/explore/charts?country=US", {}),

        # Search endpoints
        ("/api/v1/search/?q=cumbia&limit=10", {}),

        # Stream endpoints
        ("/api/v1/stream/rMbATaj7Il8", {}),
        ("/api/v1/stream/batch?ids=rMbATaj7Il8,TEST123", {}),

        # Stats endpoints
        ("/api/v1/stats/stats", {}),
    ]

    for endpoint, headers, method="GET", data=None in test_cases:
        headers = headers or {}
        response = client.request(method, endpoint, headers=headers, json=data)
        print(f"{method} {endpoint}: {response.status_code}")
        assert response.status_code in [200, 201, 204], f"Failed: {endpoint}"

# tests/test_stream_proxies.py
async def test_stream_proxy():
    """Test stream proxy functionality."""
    video_id = "rMbATaj7Il8"

    response = client.get(f"/api/v1/stream/proxy/{video_id}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "audio/mpeg"

    # Verify audio content
    content = response.content[:100]
    assert len(content) > 0
```

### Performance Tests

```python
# tests/test_performance.py
import pytest
import time

@pytest.mark.asyncio
async def test_stream_url_caching_performance():
    """Test that cache significantly improves performance."""
    video_id = "rMbATaj7Il8"

    # First call - should be slow (fetch from YouTube)
    start = time.time()
    url1 = await stream_service.get_stream_url(video_id, bypass_cache=False)
    first_call_time = time.time() - start
    assert first_call_time > 2.0  # Should take >2 seconds

    # Second call - should be fast (use cache)
    start = time.time()
    url2 = await stream_service.get_stream_url(video_id, bypass_cache=False)
    second_call_time = time.time() - start
    assert second_call_time < 0.1  # Should be <100ms

    print(f"First call: {first_call_time:.2f}s")
    print(f"Second call: {second_call_time:.2f}s")
    print(f"Speedup: {first_call_time / second_call_time:.1f}x")

@pytest.mark.asyncio
async def test_batch_stream_processing():
    """Test batch processing performance."""
    video_ids = ["rMbATaj7Il8", "TEST123", "VIDEO456"]

    start = time.time()
    results = await stream_service.get_batch_stream_urls(video_ids)
    batch_time = time.time() - start

    assert len(results) == len(video_ids)
    assert batch_time < 10.0  # Should complete within 10 seconds

    print(f"Batch processing: {batch_time:.2f}s for {len(video_ids)} videos")
```

### Load Tests

```python
# tests/test_load.py
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_stream_requests():
    """Test handling of concurrent stream requests."""
    video_id = "rMbATaj7Il8"

    # Simulate 50 concurrent requests
    tasks = [
        stream_service.get_stream_url(video_id)
        for _ in range(50)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start

    # All should succeed
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0

    # Should complete quickly due to caching
    assert elapsed < 5.0

    print(f"50 concurrent requests: {elapsed:.2f}s")

@pytest.mark.asyncio
async def test_cache_under_load():
    """Test cache performance under load."""
    video_ids = [f"VIDEO{i}" for i in range(100)]

    # Initial fetch (uncached)
    start = time.time()
    results = await stream_service.get_batch_stream_urls(video_ids)
    fetch_time = time.time() - start

    assert len([r for r in results if r.startswith("http")]) == 100

    # Cached fetch (should be much faster)
    start = time.time()
    results = await stream_service.get_batch_stream_urls(video_ids)
    cache_time = time.time() - start

    speedup = fetch_time / cache_time
    print(f"Initial fetch: {fetch_time:.2f}s")
    print(f"Cached fetch: {cache_time:.2f}s")
    print(f"Speedup: {speedup:.1f}x")
    assert speedup > 5.0  # Should be at least 5x faster
```

---

## ⏱️ TIME ESTIMATES

### Phase 1: OAuth Configuration (2-3 hours)
- Set up Google Cloud Console OAuth: 30 min
- Create OAuth credentials: 15 min
- Configure environment variables: 15 min
- Test OAuth authentication: 1 hour
- Write unit tests: 1 hour

### Phase 2: Browse/Explore/Playlists Service Fixes (4-6 hours)
- Fix Browse service with retry logic: 2 hours
- Fix Explore service: 1 hour
- Implement Podcasts service: 1.5 hours
- Fix Playlists service: 0.5 hour
- Write integration tests: 1 hour

### Phase 3: Search Service Improvements (1-2 hours)
- Fix search with error handling: 1 hour
- Implement search caching: 0.5 hour
- Write tests: 0.5 hour

### Phase 4: Stream Service Optimization (3-4 hours)
- Optimize cache TTLs: 0.5 hour
- Improve yt-dlp configuration: 1 hour
- Fix stream URL extraction: 1 hour
- Fix proxy endpoint: 0.5 hour
- Fix cache info endpoint: 0.5 hour
- Write performance tests: 0.5 hour

### Phase 5: Background Cache Refresher (2-3 hours)
- Implement background refresh: 1 hour
- Implement metadata expiry check: 1 hour
- Test background tasks: 1 hour

### Phase 6: API Endpoints Fixes (2-3 hours)
- Fix auth endpoints: 0.5 hour
- Fix podcasts endpoints: 1 hour
- Fix stream proxy: 0.5 hour

### Phase 7: Testing & Validation (3-4 hours)
- Run all unit tests: 1 hour
- Run integration tests: 1 hour
- Run load tests: 0.5 hour
- Performance optimization: 1 hour

### Phase 8: Documentation & Cleanup (1-2 hours)
- Update README: 0.5 hour
- Update API documentation: 0.5 hour
- Clean up code: 0.5 hour

**Total Estimated Time: 18-28 hours (2.5-4 working days)**

---

## 🎯 EXPECTED OUTCOMES

### Before Fix (Current State)
```
Total Endpoints: 38
Passing: 9 (23.7%)
Failing: 27 (71.1%)
- Auth: 5/5 failing (403 errors)
- Browse: 7/8 failing (YouTube Music API errors)
- Explore: 5/5 failing (YouTube Music API errors)
- Search: 3/3 failing (JSON parse errors)
- Playlists: 1/1 failing (YouTube Music API errors)
- Watch: 1/1 failing (307 redirect)
- Podcasts: 5/5 failing (404 - not implemented)
- Stream: 5/8 passing (3/3 failing - cache/proxy issues)
```

### After Fix (Target State)
```
Total Endpoints: 38
Passing: 36 (94.7%)
Failing: 2 (5.3%)
- Auth: 5/5 passing (proper OAuth authentication)
- Browse: 8/8 passing (reliable YouTube Music API calls)
- Explore: 5/5 passing (reliable YouTube Music API calls)
- Search: 3/3 passing (proper error handling)
- Playlists: 1/1 passing (reliable YouTube Music API calls)
- Watch: 1/1 passing (fix 307 redirect → 200)
- Podcasts: 5/5 passing (fully implemented)
- Stream: 8/8 passing (optimized caching + working proxy)
- Stats: 1/1 passing (unchanged)
- Uploads: 1/1 passing (returns 501 as expected)
```

### Performance Improvements

#### Response Time
- **First stream URL request:** 2-5 seconds (unchanged - YouTube API is slow)
- **Cached stream URL request:** <100ms (improved from current)
- **Batch stream URLs:** 5-10 seconds (parallel processing)
- **Search queries:** 1-2 seconds (with caching)
- **Browse endpoints:** 1-3 seconds (with caching)

#### Cache Efficiency
- **Metadata cache hit rate:** >90%
- **Stream URL cache hit rate:** >85%
- **Average response time with cache:** 3x faster than without cache
- **YouTube API calls reduced by:** ~85% with caching

#### Reliability Improvements
- **Circuit breaker prevents cascading failures:** ✅
- **Exponential backoff on API failures:** ✅
- **Graceful fallback to anonymous mode:** ✅
- **Background cache refresh:** ✅
- **Error rate:** <1% (from current ~70%)

### Functional Improvements

#### Authentication
- ✅ Proper OAuth 2.0 authentication
- ✅ Admin key validation for all protected endpoints
- ✅ Browser-based OAuth flow for first-time setup
- ✅ Graceful fallback to anonymous mode

#### Browsing & Search
- ✅ Reliable YouTube Music API integration
- ✅ Search with proper error handling
- ✅ Browse with retry logic
- ✅ Pagination support
- ✅ Categorized results

#### Streaming
- ✅ Optimized stream URL extraction
- ✅ Intelligent caching (20h metadata, 5h stream URLs)
- ✅ Background cache refresh
- ✅ Working proxy endpoint
- ✅ Batch processing support

#### Podcasts
- ✅ Full podcast endpoint implementation
- ✅ Channel information retrieval
- ✅ Episode listing
- ✅ Episode detail retrieval

#### Documentation
- ✅ Complete API documentation
- ✅ Usage examples
- ✅ Error handling documentation
- ✅ Setup instructions

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All performance tests passing
- [ ] Code coverage >80%
- [ ] Security audit completed
- [ ] Environment variables configured
- [ ] Redis connection verified
- [ ] OAuth credentials verified

### Deployment Steps

1. **Backup Current Code**
   ```bash
   git checkout -b backup-$(date +%Y%m%d)
   git add .
   git commit -m "Backup before implementation"
   git push origin backup-$(date +%Y%m%d)
   ```

2. **Update Dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   # Update .env with new settings
   # Ensure all required variables are set
   ```

4. **Test in Staging**
   ```bash
   docker-compose -f docker-compose.dev.yml up
   pytest tests/ -v --tb=short
   ```

5. **Deploy to Production**
   ```bash
   # Build and deploy
   docker-compose build
   docker-compose up -d

   # Verify deployment
   curl http://localhost:8000/health
   ```

6. **Monitor After Deployment**
   ```bash
   # Check logs
   docker-compose logs -f app

   # Run health check
   curl http://localhost:8000/health

   # Run endpoint tests
   pytest tests/test_endpoints.py -v
   ```

### Post-Deployment Validation

- [ ] All 38 endpoints returning 200 or expected status codes
- [ ] Admin key authentication working
- [ ] OAuth authentication working
- [ ] Stream URLs being cached correctly
- [ ] Background cache refresh working
- [ ] Performance metrics within acceptable range
- [ ] Error rate <1%
- [ ] No memory leaks or performance degradation
- [ ] Redis connection stable

---

## 📚 REFERENCES & RESOURCES

### Documentation
- [YouTube Music API Docs](https://ytmusicapi.readthedocs.io/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Documentation](https://redis.io/docs/)

### OAuth Setup Guide
1. Google Cloud Console: https://console.cloud.google.com/
2. OAuth 2.0 Playground: https://developers.google.com/oauthplayground
3. YouTube Data API v3: https://developers.google.com/youtube/v3/docs

### Best Practices
- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Caching Strategies: https://redis.io/docs/manual/patterns/caching/
- Retry Patterns: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

---

## 🎉 SUCCESS CRITERIA

### Technical Success
- ✅ 94.7% endpoint success rate (36/38 passing)
- ✅ Zero authentication errors
- ✅ Zero YouTube Music API errors
- ✅ Stream URLs cached efficiently
- ✅ Background cache refresh working
- ✅ Performance improvements >3x with cache

### User Success
- ✅ All 38 endpoints working reliably
- ✅ Stream URLs load in <100ms with cache
- ✅ Search and browse working properly
- ✅ Podcast functionality fully functional
- ✅ No visible errors or timeouts

### Operational Success
- ✅ Zero downtime during deployment
- ✅ Monitoring in place
- ✅ Logging configured
- ✅ Error handling comprehensive
- ✅ Documentation complete

---

## 📝 NOTES

### Future Enhancements
1. Add rate limiting per user/IP
2. Add admin dashboard for cache management
3. Implement playlist collaboration features
4. Implement webhook notifications
5. Add support for more audio formats

### Known Limitations
- YouTube Music API has daily quota limit (100k units/day)
- Stream URLs expire after ~6-12 hours
- Anonymous mode has limited functionality
- No support for YouTube Premium features

---

**End of Implementation Plan**

*This plan is comprehensive, actionable, and ready for immediate implementation. Follow each phase in order for best results.*
