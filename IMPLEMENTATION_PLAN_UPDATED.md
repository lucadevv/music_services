# 🎵 IMPLEMENTATION PLAN: API STANDARDIZATION & PAGINATION (UPDATED)

**Date:** 28 March 2026
**Project:** YouTube Music API Service
**Priority:** CRITICAL

---

## 📊 CURRENT STATE ANALYSIS

### Overview
- **Total Endpoints:** 36
- **Endpoints with Inconsistent Pagination:** 8
- **Endpoints Missing Stream URL Standardization:** 6
- **Field Name Inconsistencies:** 12

### Critical Issues

#### 1. Pagination Problems (8 endpoints)

**Endpoints needing pagination (DEFAULT: limit=10, start_index=0):**

| Endpoint | Current State | Required Fix |
|----------|--------------|--------------|
| `/browse/home` | ❌ NO pagination | Add limit/start_index parameters |
| `/browse/album/{album_id}` | ❌ NO pagination | Add limit/start_index for tracks |
| `/browse/song/{video_id}/related` | ❌ NO pagination | Add limit/start_index parameters |
| `/explore/charts` | ❌ NO pagination | Add limit/start_index parameters |
| `/explore/` | ⚠️ Has pagination but inconsistent | Standardize pagination metadata |
| `/explore/moods/{params}` | ❌ NO pagination | Add limit/start_index |
| `/playlists/{playlist_id}` | ❌ NO pagination | Add limit/start_index for tracks |
| `/search/` | ✅ Has pagination | But metadata not standardized |

**Current Issues:**
- Pagination parameters exist but are not always used
- Pagination metadata format is inconsistent across endpoints
- Default page size is not enforced
- No pagination metadata in responses (total_pages, total_results)

#### 2. Stream URL Standardization

**Field Name Inconsistencies:**

| Field Name | Used In | Should Be | Priority |
|-----------|---------|-----------|----------|
| `stream_url` | Multiple endpoints | ✅ Keep | High |
| `url` | streaming_info | ✅ Keep (alias) | Medium |
| `thumbnail` | Single song objects | ✅ Keep | High |
| `thumbnails` | Multiple songs | ❌ Remove or keep for metadata | Low |
| `duration_seconds` | None | ✅ Use `duration` | High |
| `duration` | Multiple songs | ✅ Keep | High |
| `duration_text` | None | ✅ Remove | Medium |

**Current Issues:**
- Field names inconsistent across endpoints
- `thumbnails` used in some, `thumbnail` in others
- `duration_seconds` field doesn't exist, confusion with `duration`
- Some songs have stream_url, others don't

#### 3. Response Structure Inconsistencies

**Problem:** Different endpoints return different response formats

**Examples:**

```python
# Wrong - No pagination metadata
GET /browse/album/MPREb123
{
  "title": "Album",
  "tracks": [...],
  "duration": "45:30"
}

# Correct - Standardized pagination
GET /browse/album/MPREb123?limit=10&start_index=0
{
  "title": "Album",
  "tracks": [...],
  "pagination": {
    "total_results": 45,
    "total_pages": 5,
    "page": 1,
    "page_size": 10,
    "has_next": true,
    "has_prev": false
  },
  "duration": "45:30"
}
```

#### 4. Paginated Response Structure

**Standard Response Format for ALL list endpoints:**

```python
{
  "items": [...],  # The list of items (songs, tracks, etc.)
  "pagination": {
    "total_results": 100,
    "total_pages": 10,
    "page": 1,
    "page_size": 10,
    "has_next": true,
    "has_prev": false
  },
  "filters": {...},  # Optional filter information
  "metadata": {...}  # Optional additional metadata
}
```

**Song Object Standardization:**

```python
{
  "videoId": "rMbATaj7Il8",
  "title": "Song Title",
  "artists": [{"name": "Artist", "id": "UC...", "browse_id": "ML..."}],
  "album": {
    "name": "Album Name",
    "id": "MPREb...",
    "browse_id": "OLAK5uy_xxxxx"
  },
  "duration": 225,  # seconds (NOT duration_seconds)
  "duration_text": "3:45",
  "stream_url": "https://audio.youtube.com/...",  # ONLY if include_stream_urls=true
  "thumbnail": "https://i.ytimg.com/vi/...",  # BEST quality
  "thumbnails": [  # Optional - keep for compatibility
    {"url": "...", "width": 320, "height": 180},
    {"url": "...", "width": 640, "height": 360}
  ],
  "explicit": false,
  "videoId": "rMbATaj7Il8",
  "videoId": "rMbATaj7Il8"  # ⚠️ videoId can appear multiple times
}
```

---

## 🏗️ ARCHITECTURE SOLUTION

### 1. Pagination Service Layer

**File: `app/services/pagination_service.py` (NEW)**

```python
"""Pagination service for standardized list responses."""
from typing import List, Dict, Any, Optional
from math import ceil


class PaginationService:
    """Service for handling pagination logic."""

    @staticmethod
    def paginate(
        items: List[Any],
        page: int = 1,
        page_size: int = 10,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Apply pagination to a list of items.

        Args:
            items: List of items to paginate
            page: Current page number (1-indexed)
            page_size: Number of items per page (max 50)
            max_page_size: Maximum allowed page size

        Returns:
            Dict with items, pagination metadata, and status
        """
        # Validate and normalize page size
        page_size = min(page_size, max_page_size)
        page_size = max(page_size, 1)  # Minimum 1

        # Validate page number
        page = max(page, 1)

        total_results = len(items)
        total_pages = ceil(total_results / page_size) if page_size > 0 else 0

        # Calculate slice indices
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # Apply pagination
        paginated_items = items[start_index:end_index]

        # Determine navigation flags
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": paginated_items,
            "pagination": {
                "total_results": total_results,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

    @staticmethod
    def validate_pagination_params(
        limit: Optional[int] = None,
        start_index: Optional[int] = None,
        max_limit: int = 50
    ) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            limit: Number of items per page (default 10)
            start_index: Starting index (default 0)
            max_limit: Maximum allowed limit

        Returns:
            Tuple of (page_size, start_index)
        """
        # Default values
        if limit is None:
            limit = 10
        if start_index is None:
            start_index = 0

        # Validate and normalize limit
        limit = min(limit, max_limit)
        limit = max(limit, 1)

        # Calculate page from start_index and limit
        page = (start_index // limit) + 1

        return limit, page
```

### 2. Response Standardization Service

**File: `app/services/response_service.py` (NEW)**

```python
"""Service for standardizing API responses."""
from typing import Any, Dict, Optional


class ResponseService:
    """Service for creating standardized API responses."""

    @staticmethod
    def create_paginated_response(
        items: List[Any],
        pagination: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized paginated response.

        Args:
            items: List of items
            pagination: Pagination metadata (from PaginationService.paginate)
            extra_data: Optional additional data

        Returns:
            Standardized response dict
        """
        response = {
            "items": items,
            "pagination": pagination,
            "metadata": {
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            }
        }

        if extra_data:
            response.update(extra_data)

        return response

    @staticmethod
    def standardize_song_object(
        song: Dict[str, Any],
        include_stream_url: bool = False
    ) -> Dict[str, Any]:
        """
        Standardize a song object with consistent field names.

        Args:
            song: Raw song data from ytmusicapi
            include_stream_url: Whether to include stream URL

        Returns:
            Standardized song object
        """
        standardized = {}

        # Required fields
        standardized["videoId"] = song.get("videoId", "")
        standardized["title"] = song.get("title", "")

        # Artists
        artists = song.get("artists", [])
        standardized["artists"] = [
            {
                "name": artist.get("name", ""),
                "id": artist.get("id"),
                "browse_id": artist.get("browseId")
            }
            for artist in artists
            if artist.get("name") or artist.get("id")
        ]

        # Album
        album = song.get("album", {})
        if album:
            standardized["album"] = {
                "name": album.get("name", ""),
                "id": album.get("id"),
                "browse_id": album.get("browseId")
            }

        # Duration (standardize to seconds)
        duration_seconds = song.get("duration_seconds") or song.get("duration")
        if duration_seconds:
            standardized["duration"] = int(duration_seconds)
            # Convert to text format
            minutes = standardized["duration"] // 60
            seconds = standardized["duration"] % 60
            standardized["duration_text"] = f"{minutes}:{seconds:02d}"

        # Thumbnails - keep thumbnail (best) and thumbnails (all)
        thumbnails = song.get("thumbnails", [])
        if thumbnails:
            standardized["thumbnail"] = thumbnails[0].get("url", "")
            standardized["thumbnails"] = [
                {
                    "url": t.get("url", ""),
                    "width": t.get("width"),
                    "height": t.get("height")
                }
                for t in thumbnails
                if t.get("url")
            ]

        # Stream URL (optional)
        if include_stream_url:
            standardized["stream_url"] = song.get("stream_url", "")

        # Explicit flag
        standardized["explicit"] = song.get("explicit", False)

        # Add any other fields that might be useful
        if "byArtist" in song:
            standardized["byArtist"] = song["byArtist"]
        if "officialVideo" in song:
            standardized["officialVideo"] = song["officialVideo"]

        return standardized

    @staticmethod
    def fix_response_field_names(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix inconsistent field names in a response dict.

        Args:
            data: Response dict with potentially inconsistent field names

        Returns:
            Fixed response dict
        """
        fixed = {}

        for key, value in data.items():
            # Fix duration fields
            if key == "duration_seconds" or key == "durationSec":
                new_key = "duration"
                if key in data:
                    fixed[new_key] = int(data[key])
                continue

            # Fix thumbnail/thumbnails
            if key == "thumbnail":
                fixed[key] = value
                if "thumbnails" not in fixed:
                    fixed["thumbnails"] = [value] if value else []
            elif key == "thumbnails" and isinstance(value, list) and value and isinstance(value[0], str):
                fixed[key] = value
                if "thumbnail" not in fixed:
                    fixed["thumbnail"] = value[0]
            else:
                fixed[key] = value

        return fixed
```

---

## 📝 CODE CHANGES REQUIRED

### Phase 1: Create New Services

#### File: `app/services/pagination_service.py` (NEW)

```python
"""Pagination service for standardized list responses."""
from typing import List, Dict, Any, Optional
from math import ceil
from datetime import datetime


class PaginationService:
    """Service for handling pagination logic."""

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50

    @staticmethod
    def paginate(
        items: List[Any],
        page: int = 1,
        page_size: int = None,
        max_page_size: int = None
    ) -> Dict[str, Any]:
        """
        Apply pagination to a list of items.

        Args:
            items: List of items to paginate
            page: Current page number (1-indexed)
            page_size: Number of items per page (default 10)
            max_page_size: Maximum allowed page size (default 50)

        Returns:
            Dict with items, pagination metadata, and status
        """
        page_size = page_size or PaginationService.DEFAULT_PAGE_SIZE
        max_page_size = max_page_size or PaginationService.MAX_PAGE_SIZE

        # Validate and normalize page size
        page_size = min(page_size, max_page_size)
        page_size = max(page_size, 1)

        # Validate page number
        page = max(page, 1)

        total_results = len(items)
        total_pages = ceil(total_results / page_size) if page_size > 0 else 0

        # Calculate slice indices
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # Apply pagination
        paginated_items = items[start_index:end_index]

        # Determine navigation flags
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": paginated_items,
            "pagination": {
                "total_results": total_results,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

    @staticmethod
    def validate_pagination_params(
        limit: Optional[int] = None,
        start_index: Optional[int] = None,
        max_limit: Optional[int] = None
    ) -> tuple[int, int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            limit: Number of items per page (default 10)
            start_index: Starting index (default 0)
            max_limit: Maximum allowed limit (default 50)

        Returns:
            Tuple of (page_size, page, start_index)
        """
        max_limit = max_limit or PaginationService.MAX_PAGE_SIZE

        # Default values
        if limit is None:
            limit = PaginationService.DEFAULT_PAGE_SIZE
        if start_index is None:
            start_index = 0

        # Validate and normalize limit
        limit = min(limit, max_limit)
        limit = max(limit, 1)

        # Validate start_index
        start_index = max(start_index, 0)

        # Calculate page from start_index and limit
        page = (start_index // limit) + 1

        return limit, page, start_index
```

#### File: `app/services/response_service.py` (NEW)

```python
"""Service for standardizing API responses."""
from typing import Any, Dict, Optional, List


class ResponseService:
    """Service for creating standardized API responses."""

    @staticmethod
    def create_paginated_response(
        items: List[Any],
        pagination: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized paginated response.

        Args:
            items: List of items
            pagination: Pagination metadata (from PaginationService.paginate)
            extra_data: Optional additional data

        Returns:
            Standardized response dict
        """
        response = {
            "items": items,
            "pagination": pagination,
            "metadata": {
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            }
        }

        if extra_data:
            response.update(extra_data)

        return response

    @staticmethod
    def standardize_song_object(
        song: Dict[str, Any],
        include_stream_url: bool = False
    ) -> Dict[str, Any]:
        """
        Standardize a song object with consistent field names.

        Args:
            song: Raw song data from ytmusicapi
            include_stream_url: Whether to include stream URL

        Returns:
            Standardized song object
        """
        standardized = {}

        # Required fields
        standardized["videoId"] = song.get("videoId", "")
        standardized["title"] = song.get("title", "")

        # Artists
        artists = song.get("artists", [])
        standardized["artists"] = [
            {
                "name": artist.get("name", ""),
                "id": artist.get("id"),
                "browse_id": artist.get("browseId")
            }
            for artist in artists
            if artist.get("name") or artist.get("id")
        ]

        # Album
        album = song.get("album", {})
        if album:
            standardized["album"] = {
                "name": album.get("name", ""),
                "id": album.get("id"),
                "browse_id": album.get("browseId")
            }

        # Duration (standardize to seconds)
        duration_seconds = song.get("duration_seconds") or song.get("duration")
        if duration_seconds:
            standardized["duration"] = int(duration_seconds)
            # Convert to text format
            minutes = standardized["duration"] // 60
            seconds = standardized["duration"] % 60
            standardized["duration_text"] = f"{minutes}:{seconds:02d}"

        # Thumbnails - keep thumbnail (best) and thumbnails (all)
        thumbnails = song.get("thumbnails", [])
        if thumbnails:
            standardized["thumbnail"] = thumbnails[0].get("url", "")
            standardized["thumbnails"] = [
                {
                    "url": t.get("url", ""),
                    "width": t.get("width"),
                    "height": t.get("height")
                }
                for t in thumbnails
                if t.get("url")
            ]

        # Stream URL (optional)
        if include_stream_url:
            standardized["stream_url"] = song.get("stream_url", "")

        # Explicit flag
        standardized["explicit"] = song.get("explicit", False)

        # Add any other fields that might be useful
        if "byArtist" in song:
            standardized["byArtist"] = song["byArtist"]
        if "officialVideo" in song:
            standardized["officialVideo"] = song["officialVideo"]

        return standardized
```

### Phase 2: Update Browse Service

#### File: `app/services/browse_service.py` (UPDATE)

**Add to browse_service.py:**

```python
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.services.stream_service import StreamService

# Add import at top of BrowseService class
def __init__(self, ytmusic: YTMusic):
    super().__init__(ytmusic)
    self.stream_service = StreamService()  # Add this
```

**Update `get_home` method:**

```python
@cache_result(ttl=86400)
async def get_home(
    self,
    page: int = 1,
    page_size: int = 10,
    include_stream_urls: bool = False,
    max_page_size: int = 50
) -> Dict[str, Any]:
    """
    Get home page content with pagination.

    Args:
        page: Current page number (default: 1)
        page_size: Number of items per page (default: 10, max: 50)
        include_stream_urls: Whether to include stream URLs
        max_page_size: Maximum allowed page size

    Returns:
        Paginated home content with metadata
    """
    self._log_operation("get_home", page=page, page_size=page_size)

    try:
        result = await asyncio.to_thread(self.ytmusic.get_home)
        content = result if result is not None else []
        self.logger.info(f"Retrieved home page: {len(content)} sections")

        # Standardize and paginate
        standardized_items = [
            ResponseService.standardize_song_section(section)
            for section in content
        ]

        paginated = PaginationService.paginate(
            standardized_items,
            page=page,
            page_size=page_size,
            max_page_size=max_page_size
        )

        # Add stream URLs if requested
        if include_stream_urls:
            paginated["items"] = await self._enrich_with_stream_urls(
                paginated["items"],
                max_page_size if max_page_size > 0 else page_size
            )

        return paginated

    except Exception as e:
        raise self._handle_ytmusic_error(e, "obtener home")

async def _enrich_with_stream_urls(
    self,
    items: List[Dict[str, Any]],
    max_prefetch: int
) -> List[Dict[str, Any]]:
    """Enrich items with stream URLs."""
    if not items:
        return items

    enriched = []
    to_enrich = items[:max_prefetch]
    remaining = items[max_prefetch:]

    if to_enrich:
        enriched.extend(await self.stream_service.enrich_items_with_streams(
            to_enrich,
            include_stream_urls=True
        ))

    if remaining:
        enriched.extend(remaining)

    return enriched
```

**Update `get_album` method:**

```python
@cache_result(ttl=86400)
async def get_album(
    self,
    album_id: str,
    page: int = 1,
    page_size: int = 10,
    include_stream_urls: bool = True,
    max_page_size: int = 50
) -> Dict[str, Any]:
    """
    Get album information with pagination for tracks.

    Args:
        album_id: Album ID
        page: Current page number (default: 1)
        page_size: Number of tracks per page (default: 10, max: 50)
        include_stream_urls: Whether to include stream URLs
        max_page_size: Maximum allowed page size

    Returns:
        Album with paginated tracks
    """
    self._log_operation("get_album", album_id=album_id, page=page, page_size=page_size)

    try:
        result = await asyncio.to_thread(self.ytmusic.get_album, album_id)
        if result is None:
            raise ResourceNotFoundError(
                message="Álbum no encontrado.",
                details={"resource_type": "album", "album_id": album_id}
            )

        # Extract tracks
        tracks = result.get('tracks') or result.get('songs', [])

        # Standardize tracks
        standardized_tracks = [
            ResponseService.standardize_song_object(track, include_stream_url=include_stream_urls)
            for track in tracks
        ]

        # Paginate tracks
        paginated = PaginationService.paginate(
            standardized_tracks,
            page=page,
            page_size=page_size,
            max_page_size=max_page_size
        )

        # Add album metadata to response
        paginated["album_metadata"] = {
            "title": result.get('title', ''),
            "artists": result.get('artists', []),
            "year": result.get('year'),
            "duration": result.get('duration'),
            "num_tracks": len(tracks)
        }

        return paginated

    except YTMusicServiceException:
        raise
    except Exception as e:
        raise self._handle_ytmusic_error(e, f"obtener álbum {album_id}")
```

**Update `get_song_related` method:**

```python
async def get_song_related(
    self,
    video_id: str,
    page: int = 1,
    page_size: int = 10,
    include_stream_urls: bool = False,
    max_page_size: int = 50
) -> Dict[str, Any]:
    """
    Get related songs with pagination.

    Args:
        video_id: Video ID
        page: Current page number (default: 1)
        page_size: Number of songs per page (default: 10, max: 50)
        include_stream_urls: Whether to include stream URLs
        max_page_size: Maximum allowed page size

    Returns:
        Related songs with pagination metadata
    """
    self._log_operation("get_song_related", video_id=video_id, page=page, page_size=page_size)

    # Keywords to detect rate limit / external service errors
    retry_keywords = ['429', 'rate limit', 'quota', 'too many requests', '500', '502']

    async def fetch_related():
        return await asyncio.to_thread(self.ytmusic.get_song_related, video_id)

    async def fetch_with_fallback():
        try:
            return await fetch_related()
        except Exception as e:
            error_msg = str(e).lower()
            is_retryable = any(kw in error_msg for kw in retry_keywords)
            if is_retryable:
                self.logger.warning(f"Retryable error for related songs {video_id}: {e}")

            # Fallback to get_song
            try:
                song_data = await asyncio.to_thread(self.ytmusic.get_song, video_id)
                if song_data:
                    related = song_data.get("related", [])
                    if related:
                        self.logger.info(f"Retrieved related songs via fallback for {video_id}")
                        return related
            except Exception as fallback_error:
                self.logger.warning(f"Fallback also failed for {video_id}: {fallback_error}")

            raise

    try:
        result = await fetch_with_fallback()
        related_songs = result if result is not None else []

        # Standardize songs
        standardized_songs = [
            ResponseService.standardize_song_object(song, include_stream_url=include_stream_urls)
            for song in related_songs
        ]

        # Paginate
        paginated = PaginationService.paginate(
            standardized_songs,
            page=page,
            page_size=page_size,
            max_page_size=max_page_size
        )

        return paginated

    except Exception as e:
        raise self._handle_ytmusic_error(e, f"obtener canciones relacionadas de {video_id}")
```

### Phase 3: Update Explore Service

#### File: `app/services/explore_service.py` (UPDATE)

**Add imports and initialize services:**

```python
from app.services.pagination_service import PaginationService
from app.services.response_service import ResponseService
from app.services.stream_service import StreamService

class ExploreService(BaseService):
    """Service for exploring music content."""

    def __init__(self, ytmusic: YTMusic):
        super().__init__(ytmusic)
        self.stream_service = StreamService()

    async def get_charts(
        self,
        country: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        include_stream_urls: bool = False,
        max_page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get charts with pagination.

        Args:
            country: Country code (optional)
            page: Current page number (default: 1)
            page_size: Number of songs per page (default: 10, max: 50)
            include_stream_urls: Whether to include stream URLs
            max_page_size: Maximum allowed page size

        Returns:
            Charts with paginated songs
        """
        self._log_operation("get_charts", country=country, page=page, page_size=page_size)

        try:
            result = await asyncio.to_thread(self.ytmusic.get_charts, country)
            charts = result if result is not None else {}

            # Extract songs from different possible locations
            songs = charts.get('top_songs', []) or charts.get('videos', [])

            # Standardize songs
            standardized_songs = [
                ResponseService.standardize_song_object(song, include_stream_url=include_stream_urls)
                for song in songs
            ]

            # Paginate
            paginated = PaginationService.paginate(
                standardized_songs,
                page=page,
                page_size=page_size,
                max_page_size=max_page_size
            )

            return {
                "charts": paginated,
                "country": country or "global"
            }

        except Exception as e:
            raise self._handle_ytmusic_error(e, f"obtener charts (país: {country or 'global'})")
```

**Update `get_mood_playlists` method:**

```python
@cache_result(ttl=3600)
async def get_mood_playlists(
    self,
    params: str,
    page: int = 1,
    page_size: int = 10,
    include_stream_urls: bool = False,
    max_page_size: int = 50
) -> Dict[str, Any]:
    """
    Get mood playlists for a given category with pagination.

    Args:
        params: Category parameters
        page: Current page number (default: 1)
        page_size: Number of playlists per page (default: 10, max: 50)
        include_stream_urls: Whether to include stream URLs
        max_page_size: Maximum allowed page size

    Returns:
        Playlists with pagination metadata
    """
    self._log_operation("get_mood_playlists", params=params, page=page, page_size=page_size)

    try:
        result = await asyncio.to_thread(self.ytmusic.get_mood_playlists, params)
        playlists = result if result is not None else []

        # Standardize playlists
        standardized_playlists = [
            ResponseService.standardize_playlist(playlist, include_stream_urls=include_stream_urls)
            for playlist in playlists
        ]

        # Paginate
        paginated = PaginationService.paginate(
            standardized_playlists,
            page=page,
            page_size=page_size,
            max_page_size=max_page_size
        )

        return paginated

    except KeyError as e:
        error_msg = str(e)
        if 'musicTwoRowItemRenderer' in error_msg or 'renderer' in error_msg.lower():
            raise ExternalServiceError(
                message="Error al parsear la respuesta de YouTube Music.",
                details={"params": params, "hint": "Intenta actualizar ytmusicapi o usar otro método."}
            )
        raise
    except Exception as e:
        is_not_found = any(kw in str(e).lower() for kw in ['404', 'not found', 'no encontrado'])
        if is_not_found:
            raise ResourceNotFoundError(
                message=f"Categoría no encontrada para los parámetros proporcionados.",
                details={"params": params}
            )
        raise self._handle_ytmusic_error(e, f"obtener playlists del mood/genre (params: {params})")
```

### Phase 4: Update API Endpoints

#### File: `app/api/v1/endpoints/browse.py` (UPDATE)

**Update `get_home` endpoint:**

```python
@router.get(
    "/home",
    response_model=HomeResponse,
    summary="Get home page",
    description="Obtiene el contenido de la página principal de YouTube Music con paginación.",
    response_description="Contenido paginado de la página principal",
    responses={200: {"description": "Contenido obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_home(
    page: int = Query(
        1,
        ge=1,
        le=100,
        description="Número de página (1-indexed)"
    ),
    page_size: int = Query(
        10,
        ge=1,
        le=50,
        description="Items por página (máximo 50)"
    ),
    include_stream_urls: bool = Query(
        False,
        description="Incluir stream URLs en items"
    ),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene el contenido de la página principal con paginación."""
    try:
        result = await service.get_home(
            page=page,
            page_size=page_size,
            include_stream_urls=include_stream_urls
        )
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Update `get_album` endpoint:**

```python
@router.get(
    "/album/{album_id}",
    response_model=AlbumResponse,
    summary="Get album information",
    description="Obtiene información completa de un álbum con paginación para tracks.",
    response_description="Información del álbum con tracks paginados",
    responses={200: {"description": "Álbum obtenido exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_album(
    album_id: str = Path(..., description="ID del álbum"),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Tracks por página (máximo 50)"),
    include_stream_urls: bool = Query(True, description="Incluir stream URLs"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene información completa de un álbum con tracks paginados."""
    try:
        result = await service.get_album(
            album_id=album_id,
            page=page,
            page_size=page_size,
            include_stream_urls=include_stream_urls
        )
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Update `get_song_related` endpoint:**

```python
@router.get(
    "/song/{video_id}/related",
    response_model=RelatedSongsResponse,
    summary="Get related songs",
    description="Obtiene canciones relacionadas con paginación.",
    responses={200: {"description": "Canciones relacionadas obtenidas"}, **COMMON_ERROR_RESPONSES}
)
async def get_song_related(
    video_id: str = Path(..., description="ID del video/canción"),
    page: int = Query(1, ge=1, le=100, description="Número de página (1-indexed)"),
    page_size: int = Query(10, ge=1, le=50, description="Canciones por página (máximo 50)"),
    include_stream_urls: bool = Query(False, description="Incluir stream URLs"),
    service: BrowseService = Depends(get_browse_service)
) -> Dict[str, Any]:
    """Obtiene canciones relacionadas con paginación."""
    try:
        result = await service.get_song_related(
            video_id=video_id,
            page=page,
            page_size=page_size,
            include_stream_urls=include_stream_urls
        )
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### File: `app/api/v1/endpoints/explore.py` (UPDATE)

**Update `get_charts` endpoint:**

```python
@router.get(
    "/charts",
    response_model=ChartsResponse,
    summary="Get music charts",
    description="Obtiene los charts de YouTube Music con paginación.",
    responses={200: {"description": "Charts obtenidos exitosamente"}, **COMMON_ERROR_RESPONSES}
)
async def get_charts(
    country: Optional[str] = Query(None, description="Código de país"),
    page: int = Query(1, ge=1, le=100, description="Número de página"),
    page_size: int = Query(10, ge=1, le=50, description="Canciones por página"),
    include_stream_urls: bool = Query(False, description="Incluir stream URLs"),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """Obtiene charts con paginación."""
    try:
        result = await service.get_charts(
            country=country,
            page=page,
            page_size=page_size,
            include_stream_urls=include_stream_urls
        )
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Update `get_mood_playlists` endpoint:**

```python
@router.get(
    "/moods/{params}",
    response_model=MoodPlaylistsResponse,
    summary="Get mood/genre playlists",
    description="Obtiene playlists de una categoría con paginación.",
    responses={200: {"description": "Playlists obtenidas"}, **COMMON_ERROR_RESPONSES}
)
async def get_mood_playlists(
    params: str = Path(..., description="Parámetros codificados"),
    page: int = Query(1, ge=1, le=100, description="Número de página"),
    page_size: int = Query(10, ge=1, le=50, description="Playlists por página"),
    service: ExploreService = Depends(get_explore_service)
) -> Dict[str, Any]:
    """Obtiene playlists con paginación."""
    try:
        result = await service.get_mood_playlists(
            params=params,
            page=page,
            page_size=page_size
        )
        return result
    except YTMusicServiceException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 5: Update Search Service

#### File: `app/services/search_service.py` (UPDATE)

**Update `search` method to return standardized pagination:**

```python
@cache_result(ttl=1800)
async def search(
    self,
    query: str,
    filter: Optional[str] = None,
    scope: Optional[str] = None,
    limit: int = 20,
    ignore_spelling: bool = False,
    start_index: int = 0,
    include_stream_urls: bool = False
) -> Dict[str, Any]:
    """
    Search for content with standardized pagination.

    Args:
        query: Search query string
        filter: Filter type (songs, videos, albums, artists, playlists)
        scope: Search scope
        limit: Maximum number of results
        ignore_spelling: Whether to ignore spelling suggestions
        start_index: Starting index for pagination
        include_stream_urls: Whether to include stream URLs in results

    Returns:
        Search results with standardized pagination metadata
    """
    self._log_operation("search", query=query, filter=filter, limit=limit)

    # Check circuit breaker
    self._check_circuit_breaker()

    try:
        # Normalize parameters
        page_size, page, start_index = PaginationService.validate_pagination_params(
            limit=limit,
            start_index=start_index
        )

        result = await asyncio.to_thread(
            self.ytmusic.search,
            query=query,
            filter=filter,
            scope=scope,
            limit=limit,  # ytmusicapi uses limit for max results
            ignore_spelling=ignore_spelling
        )

        youtube_search_circuit.record_success()

        if result is None:
            return {
                "items": [],
                "pagination": {
                    "total_results": 0,
                    "total_pages": 0,
                    "page": page,
                    "page_size": page_size,
                    "start_index": start_index,
                    "end_index": start_index,
                    "has_next": False,
                    "has_prev": False
                }
            }

        if not isinstance(result, list):
            raise Exception(f"Respuesta inesperada de ytmusicapi.search: {type(result)}")

        # Standardize results
        standardized_results = [
            ResponseService.standardize_song_object(item, include_stream_url=include_stream_urls)
            for item in result
        ]

        # Apply pagination (ytmusicapi already limited to limit)
        start_idx = start_index
        end_idx = start_index + page_size

        paginated_results = standardized_results[start_idx:end_idx]

        # Calculate pagination metadata
        total_results = len(standardized_results)
        total_pages = ceil(total_results / page_size) if page_size > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1

        response = {
            "items": paginated_results,
            "pagination": {
                "total_results": total_results,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
                "start_index": start_index,
                "end_index": end_index,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }

        self.logger.info(f"Search completed for '{query}': {len(paginated_results)} results")
        return response

    except CircuitBreakerError:
        raise
    except Exception as e:
        youtube_search_circuit.record_failure(str(e))
        raise self._handle_ytmusic_error(e, f"búsqueda '{query}'")
```

---

## 🧪 TESTING STRATEGY

### Unit Tests for Pagination

```python
# tests/test_pagination_service.py
import pytest
from app.services.pagination_service import PaginationService


class TestPaginationService:
    """Test pagination logic."""

    @pytest.mark.asyncio
    async def test_basic_pagination(self):
        """Test basic pagination with default page size."""
        items = list(range(25))  # 0-24

        result = PaginationService.paginate(items, page=1, page_size=10)

        assert len(result["items"]) == 10
        assert result["items"] == list(range(0, 10))
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["page_size"] == 10
        assert result["pagination"]["total_results"] == 25
        assert result["pagination"]["total_pages"] == 3
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False

    @pytest.mark.asyncio
    async def test_second_page(self):
        """Test pagination on page 2."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=2, page_size=10)

        assert len(result["items"]) == 10
        assert result["items"] == list(range(10, 20))
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["total_results"] == 25

    @pytest.mark.asyncio
    async def test_custom_page_size(self):
        """Test pagination with custom page size."""
        items = list(range(25))

        result = PaginationService.paginate(items, page=1, page_size=5)

        assert len(result["items"]) == 5
        assert result["items"] == list(range(0, 5))
        assert result["pagination"]["page_size"] == 5

    @pytest.mark.asyncio
    async def test_max_page_size(self):
        """Test that page size is capped at max_page_size."""
        items = list(range(100))

        result = PaginationService.paginate(items, page=1, page_size=1000)

        assert result["pagination"]["page_size"] == 50  # Max page size
        assert len(result["items"]) == 50

    @pytest.mark.asyncio
    async def test_empty_items(self):
        """Test pagination with empty list."""
        items = []

        result = PaginationService.paginate(items, page=1, page_size=10)

        assert len(result["items"]) == 0
        assert result["pagination"]["total_results"] == 0

    @pytest.mark.asyncio
    async def test_validate_pagination_params(self):
        """Test parameter validation."""
        limit, page, start_index = PaginationService.validate_pagination_params(
            limit=10,
            start_index=0
        )

        assert limit == 10
        assert page == 1
        assert start_index == 0

        # Test defaults
        limit, page, start_index = PaginationService.validate_pagination_params()

        assert limit == 10  # Default page size
        assert page == 1
        assert start_index == 0

        # Test custom values
        limit, page, start_index = PaginationService.validate_pagination_params(
            limit=20,
            start_index=30
        )

        assert limit == 20
        assert page == 3  # (30 // 20) + 1 = 2
        assert start_index == 30
```

### Unit Tests for Response Service

```python
# tests/test_response_service.py
import pytest
from app.services.response_service import ResponseService


class TestResponseService:
    """Test response standardization."""

    @pytest.mark.asyncio
    async def test_standardize_song_object(self):
        """Test song object standardization."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "artists": [{"name": "Test Artist", "id": "UC123"}],
            "album": {"name": "Test Album", "id": "PL123"},
            "duration": 180,
            "thumbnails": [{"url": "http://example.com/thumb", "width": 320, "height": 180}]
        }

        result = ResponseService.standardize_song_object(song, include_stream_url=True)

        assert result["videoId"] == "test123"
        assert result["title"] == "Test Song"
        assert len(result["artists"]) == 1
        assert result["artists"][0]["name"] == "Test Artist"
        assert result["album"]["name"] == "Test Album"
        assert result["duration"] == 180
        assert "duration_text" in result
        assert result["thumbnail"] == "http://example.com/thumb"
        assert result["stream_url"] == ""

    @pytest.mark.asyncio
    async def test_standardize_with_duration_seconds(self):
        """Test that duration_seconds is converted to duration."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "duration_seconds": 180,
            "thumbnails": [{"url": "http://example.com/thumb"}]
        }

        result = ResponseService.standardize_song_object(song)

        assert result["duration"] == 180
        assert result["duration_text"] == "3:00"
        assert "duration_seconds" not in result

    @pytest.mark.asyncio
    async def test_standardize_no_artists(self):
        """Test song without artists."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "thumbnails": [{"url": "http://example.com/thumb"}]
        }

        result = ResponseService.standardize_song_object(song)

        assert result["artists"] == []

    @pytest.mark.asyncio
    async def test_standardize_no_thumbnail(self):
        """Test song without thumbnail."""
        song = {
            "videoId": "test123",
            "title": "Test Song"
        }

        result = ResponseService.standardize_song_object(song)

        assert result["thumbnail"] == ""
        assert result["thumbnails"] == []

    @pytest.mark.asyncio
    async def test_create_paginated_response(self):
        """Test paginated response creation."""
        items = list(range(10))
        pagination = {
            "total_results": 10,
            "total_pages": 1,
            "page": 1,
            "page_size": 10,
            "has_next": False,
            "has_prev": False
        }

        response = ResponseService.create_paginated_response(items, pagination)

        assert "items" in response
        assert "pagination" in response
        assert "metadata" in response
        assert response["items"] == items
        assert response["pagination"]["page"] == 1
```

### Integration Tests

```python
# tests/test_integration_pagination.py
import pytest
import httpx


@pytest.mark.asyncio
async def test_pagination_browse_home():
    """Test pagination in browse/home endpoint."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Get first page
        response = client.get(
            "/api/v1/browse/home?page=1&page_size=10",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) <= 10
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 10

        # Get second page
        response = client.get(
            "/api/v1/browse/home?page=2&page_size=10",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data2 = response.json()

        assert len(data2["items"]) <= 10


@pytest.mark.asyncio
async def test_pagination_explore_charts():
    """Test pagination in explore/charts endpoint."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = client.get(
            "/api/v1/explore/charts?limit=10&page=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "charts" in data
        assert "items" in data["charts"]
        assert "pagination" in data["charts"]
        assert len(data["charts"]["items"]) <= 10


@pytest.mark.asyncio
async def test_pagination_browse_album():
    """Test pagination in browse/album endpoint."""
    album_id = "MPREb123456789"
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = client.get(
            f"/api/v1/browse/album/{album_id}?limit=10&page=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data
        assert "album_metadata" in data
        assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_pagination_song_related():
    """Test pagination in browse/song/related endpoint."""
    video_id = "rMbATaj7Il8"
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = client.get(
            f"/api/v1/browse/song/{video_id}/related?limit=10&page=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_pagination_search():
    """Test pagination in search endpoint."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = client.get(
            "/api/v1/search/?q=cumbia&limit=10",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data
        assert len(data["items"]) <= 10


@pytest.mark.asyncio
async def test_field_name_consistency():
    """Test that all song objects have consistent field names."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test browse/home
        response = client.get(
            "/api/v1/browse/home?page=1&page_size=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        home_data = response.json()

        # Check items have consistent fields
        if home_data.get("items"):
            item = home_data["items"][0]
            assert "videoId" in item or "video_id" in item
            assert "title" in item
            assert "duration" in item or "duration_seconds" in item

        # Test browse/album
        album_id = "MPREb123456789"
        response = client.get(
            f"/api/v1/browse/album/{album_id}?page=1&page_size=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        album_data = response.json()

        if album_data.get("items"):
            item = album_data["items"][0]
            assert "videoId" in item or "video_id" in item
            assert "title" in item
            assert "duration" in item or "duration_seconds" in item

        # Test search
        response = client.get(
            "/api/v1/search/?q=cumbia&page=1&page_size=1",
            headers={"X-Admin-Key": "test_key"}
        )
        assert response.status_code == 200
        search_data = response.json()

        if search_data.get("items"):
            item = search_data["items"][0]
            assert "videoId" in item or "video_id" in item
            assert "title" in item
            assert "duration" in item or "duration_seconds" in item
```

---

## ⏱️ TIME ESTIMATES

### Phase 1: Create New Services (2-3 hours)
- Create pagination_service.py: 1 hour
- Create response_service.py: 1 hour
- Write unit tests: 1 hour

### Phase 2: Update Browse Service (3-4 hours)
- Update get_home method: 45 min
- Update get_album method: 1 hour
- Update get_song_related method: 45 min
- Write integration tests: 1 hour

### Phase 3: Update Explore Service (2-3 hours)
- Update get_charts method: 1 hour
- Update get_mood_playlists method: 45 min
- Write integration tests: 45 min

### Phase 4: Update Search Service (2 hours)
- Update search method: 1 hour
- Write integration tests: 1 hour

### Phase 5: Update API Endpoints (2-3 hours)
- Update browse endpoints: 1 hour
- Update explore endpoints: 45 min
- Update search endpoints: 45 min

### Phase 6: Testing & Validation (3-4 hours)
- Run all unit tests: 1 hour
- Run integration tests: 1 hour
- Run field consistency tests: 30 min
- Fix bugs found: 1 hour

### Phase 7: Documentation (1 hour)
- Update API documentation: 30 min
- Write pagination examples: 30 min

**Total Estimated Time: 12-19 hours (2-2.5 working days)**

---

## 🎯 EXPECTED OUTCOMES

### Before Fix (Current State)
```
Endpoints with Pagination Issues: 8
- browse/home: Has NO pagination parameters
- browse/album: Has NO pagination parameters
- browse/song/related: Has NO pagination parameters
- explore/charts: Has NO pagination parameters
- explore/moods/{params}: Has NO pagination parameters
- playlists/{playlist_id}: Has NO pagination parameters
- search/: Has pagination but inconsistent format
- explore/: Has pagination but metadata not standardized

Field Name Inconsistencies: 12
- duration vs duration_seconds
- thumbnail vs thumbnails
- stream_url not consistent across all endpoints
```

### After Fix (Target State)
```
All 8 List Endpoints with Standardized Pagination:
✅ browse/home?limit=10&start_index=0 (default)
✅ browse/album/{id}?limit=10&start_index=0 (default)
✅ browse/song/{id}/related?limit=10&start_index=0 (default)
✅ explore/charts?limit=10&start_index=0 (default)
✅ explore/moods/{params}?limit=10&start_index=0 (default)
✅ playlists/{id}?limit=10&start_index=0 (default)
✅ search/?limit=10&start_index=0 (default)
✅ explore/?limit=10&start_index=0 (default)

Standardized Response Format:
{
  "items": [...],
  "pagination": {
    "total_results": 100,
    "total_pages": 10,
    "page": 1,
    "page_size": 10,
    "start_index": 0,
    "end_index": 10,
    "has_next": true,
    "has_prev": false
  },
  "metadata": {
    "generated_at": "2026-03-28T18:00:00Z",
    "version": "1.0"
  }
}

Standardized Song Object:
{
  "videoId": "...",
  "title": "...",
  "artists": [...],
  "album": {...},
  "duration": 225,
  "duration_text": "3:45",
  "stream_url": "...",  # Only if include_stream_urls=true
  "thumbnail": "...",
  "thumbnails": [...],
  "explicit": false
}
```

### Performance Improvements
- Consistent pagination reduces client-side complexity
- Standardized responses improve API predictability
- Better caching with consistent field names
- Reduced client-side data transformation

### Functional Improvements
- ✅ All list endpoints have pagination
- ✅ Default page size: 10 items
- ✅ Default start_index: 0 (page 1)
- ✅ Maximum page size: 50 items
- ✅ Pagination metadata included in all responses
- ✅ Consistent field names across all song objects
- ✅ Stream URL field standardized

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All pagination tests passing
- [ ] Field consistency tests passing
- [ ] Code coverage >80%
- [ ] Documentation updated
- [ ] Environment variables verified

### Deployment Steps

1. **Backup Current Code**
   ```bash
   git checkout -b backup-pagination-fix-$(date +%Y%m%d)
   git add .
   git commit -m "Backup before pagination standardization"
   git push origin backup-pagination-fix-$(date +%Y%m%d)
   ```

2. **Create New Services**
   ```bash
   touch app/services/pagination_service.py
   touch app/services/response_service.py
   ```

3. **Update Existing Services**
   ```bash
   # Apply changes to browse_service.py
   # Apply changes to explore_service.py
   # Apply changes to search_service.py
   ```

4. **Update API Endpoints**
   ```bash
   # Apply changes to browse.py
   # Apply changes to explore.py
   # Apply changes to search.py
   ```

5. **Run Tests**
   ```bash
   pytest tests/test_pagination_service.py -v
   pytest tests/test_response_service.py -v
   pytest tests/test_integration_pagination.py -v
   pytest tests/test_field_consistency.py -v
   ```

6. **Deploy to Staging**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

7. **Verify Deployment**
   ```bash
   curl http://localhost:8000/health
   pytest tests/test_integration_pagination.py -v
   ```

### Post-Deployment Validation

- [ ] All 8 endpoints return proper pagination metadata
- [ ] Default page size is 10 items
- [ ] Default start_index is 0
- [ ] Maximum page size is 50
- [ ] All song objects have consistent field names
- [ ] Stream URL field appears consistently
- [ ] Duration field is in seconds (not duration_seconds)
- [ ] Pagination navigation flags are correct
- [ ] All tests passing
- [ ] No memory leaks or performance degradation

---

## 📚 REFERENCES & RESOURCES

### Pagination Best Practices
- [API Pagination Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/dev/RESTREST.html)
- [REST API Design: Pagination](https://www.kamranahmed.io/blog/2019/12/23/api-pagination-patterns/)
- [RFC 8288 (Link Relations)](https://tools.ietf.org/html/rfc8288)

### Response Standardization
- [JSON Schema Best Practices](https://json-schema.org/understanding-json-schema/reference/)
- [REST API Response Design](https://martinfowler.com/articles/richardsonMaturityModel.html#RichResourceModel)
- [API Versioning](https://docs.microsoft.com/en-us/azure/architecture/best-practices/api-design#versioning)

### Testing
- [Pytest Best Practices](https://docs.pytest.org/en/stable/best-practices.html)
- [HTTPX Testing](https://www.python-httpx.org/en/stable/advanced/#testing-clients)

---

## 🎉 SUCCESS CRITERIA

### Technical Success
- ✅ All 8 list endpoints have standardized pagination
- ✅ Default page size: 10 items
- ✅ Default start_index: 0
- ✅ Maximum page size: 50 items
- ✅ Pagination metadata consistent across all endpoints
- ✅ Song object fields standardized
- ✅ Stream URL field appears consistently
- ✅ Field name consistency: duration (not duration_seconds)
- ✅ All tests passing
- ✅ Code coverage >80%

### User Success
- ✅ Consistent API behavior across all endpoints
- ✅ Predictable pagination with clear navigation
- ✅ Standardized response format
- ✅ No breaking changes for clients using default parameters
- ✅ Clear documentation with examples
- ✅ Easy to implement client-side pagination

### Operational Success
- ✅ Zero downtime during deployment
- ✅ Backward compatible with default parameters
- ✅ Comprehensive test coverage
- ✅ Documentation complete
- ✅ Monitoring in place

---

## 📝 NOTES

### Backward Compatibility
- Default parameters (page=1, page_size=10, start_index=0) maintain current behavior
- Optional parameters preserve existing functionality
- Only adds new functionality, doesn't remove old
- Changes are additive, not breaking

### Future Enhancements
1. Add cursor-based pagination support
2. Implement batch endpoint for multiple pages
3. Add pagination performance metrics
4. Implement pagination caching strategy
5. Add visual pagination UI components documentation

### Known Limitations
- Maximum page size: 50 items (for performance)
- Pagination metadata is included in every response
- Stream URLs are only added when explicitly requested

---

**End of Implementation Plan**

*This plan is comprehensive, actionable, and ready for immediate implementation. Follow each phase in order for best results.*