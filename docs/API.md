# API Documentation - YouTube Music Service

Complete API reference for the YouTube Music Service built with FastAPI.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

### Music Endpoints Authentication

Endpoints under `/search/*`, `/browse/*`, `/explore/*`, `/playlists/*`, `/watch/*`, `/stream/*`, and `/podcasts/*` require:

- `Authorization: Bearer <api_key>`

Example:

```bash
curl -H "Authorization: Bearer sk_live_tu_api_key" \
  "http://localhost:8000/api/v1/search/?q=eminem"
```

### Admin Authentication

Endpoints under `/auth/*`, `/api-keys/*`, and `/stats/*` require an `X-Admin-Key` header configured via `ADMIN_SECRET_KEY` in `.env`.

```bash
curl -H "X-Admin-Key: mi-clave-super-secreta" \
  http://localhost:8000/api/v1/auth/status
```

---

## Endpoints Overview

| Domain | Description |
|--------|-------------|
| `/search` | Search music content |
| `/browse` | Home, artists, albums, songs, lyrics |
| `/explore` | Charts, moods/genres |
| `/stream` | Audio streaming URLs and proxy |
| `/watch` | Playlist radio/shuffle |
| `/playlists` | Public playlists |
| `/podcasts` | Channels and episodes |
| `/auth` | Admin browser/accounts |
| `/api-keys` | Admin API key management |
| `/stats` | Admin monitoring |

---

## Search

### GET /search/

Search for music content.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `query` | string | query | Search query |
| `filter` | string | query | Filter type (songs, videos, albums, artists, playlists) |
| `limit` | integer | query | Max results (default: 20) |

**Response:** `200 OK`
```json
{
  "results": [
    {
      "videoId": "dQw4w9WgXcQ",
      "title": "Song Title",
      "artists": [{"name": "Artist Name"}],
      "album": {"name": "Album Name"},
      "duration": "3:45",
      "thumbnail": "https://..."
    }
  ]
}
```

### GET /search/suggestions

Get search suggestions.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `query` | string | query | Search query |

**Response:** `200 OK`
```json
{
  "suggestions": ["song name", "artist name"]
}
```

### DELETE /search/suggestions

Remove a search suggestion.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `suggestion` | string | query | Suggestion to remove |

**Response:** `200 OK`

---

## Browse

### GET /browse/home

Get the YouTube Music home page content.

**Response:** `200 OK`
```json
{
  "contents": [...]
}
```

### GET /browse/artist/{channel_id}/albums

Get all albums from an artist.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `channel_id` | string | path | Artist channel ID |
| `params` | string | query | Pagination params |

**Response:** `200 OK`
```json
{
  "albums": [...]
}
```

### GET /browse/album/{album_id}

Get complete album information including all tracks.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `album_id` | string | path | Album ID (e.g., `MPREb...`) |
| `include_stream_urls` | boolean | query | Include stream URLs (default: true) |

**Response:** `200 OK`
```json
{
  "title": "Album Title",
  "artists": [{"name": "Artist"}],
  "tracks": [
    {
      "videoId": "rMbATaj7Il8",
      "title": "Track Title",
      "stream_url": "https://...",
      "thumbnail": "https://..."
    }
  ]
}
```

### GET /browse/album/{album_id}/browse-id

Get album browse ID from album ID.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `album_id` | string | path | Album ID |

**Response:** `200 OK`
```json
{
  "browseId": "album//..."
}
```

### GET /browse/song/{video_id}

Get song metadata.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video/song ID (11 chars) |
| `signature_timestamp` | integer | query | Signature timestamp (optional) |

**Response:** `200 OK`
```json
{
  "videoId": "rMbATaj7Il8",
  "title": "Song Title",
  "artists": [...],
  "album": {...},
  "duration": "3:45",
  "thumbnail": "https://..."
}
```

### GET /browse/song/{video_id}/related

Get related songs.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video/song ID |
| `include_stream_urls` | boolean | query | Include stream URLs (default: true) |

**Response:** `200 OK`
```json
{
  "related": [...]
}
```

### GET /browse/lyrics/{browse_id}

Get lyrics by browse ID.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `browse_id` | string | path | Browse ID |

**Response:** `200 OK`
```json
{
  "lyrics": "Line 1\nLine 2\n..."
}
```

### GET /browse/lyrics-by-video/{video_id}

Get lyrics by video ID.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK`
```json
{
  "lyrics": "..."
}
```

---

## Explore

### GET /explore/

Get explore content.

**Response:** `200 OK`
```json
{
  "moods": [...],
  "charts": [...]
}
```

### GET /explore/moods

Get mood categories.

**Response:** `200 OK`
```json
{
  "moods": [
    {
      "title": "Happy",
      "params": "mood=happy"
    }
  ]
}
```

### GET /explore/moods/{params}

Get mood playlists.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `params` | string | path | Mood parameters |

**Response:** `200 OK`
```json
{
  "playlists": [...]
}
```

### GET /explore/charts

Get charts.

**Response:** `200 OK`
```json
{
  "charts": [...]
}
```

### GET /explore/category/{params}

⚠️ **DEPRECATED** — Alias for `/explore/moods/{params}`. Returns header `Warning: 299`.

---

## Stream

### GET /stream/{video_id}

Get audio stream URL.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK`
```json
{
  "video_id": "rMbATaj7Il8",
  "url": "https://...",
  "format": "mp4",
  "bitrate": 128
}
```

### GET /stream/proxy/{video_id}

Proxy audio stream directly.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK` (audio stream)

### GET /stream/batch

Get batch stream URLs.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_ids` | string | query | Comma-separated video IDs |

**Response:** `200 OK`
```json
{
  "streams": [
    {"video_id": "...", "url": "..."}
  ]
}
```

### GET /stream/cache/stats

Get cache statistics.

**Response:** `200 OK`
```json
{
  "total_keys": 100,
  "memory_usage_mb": 50
}
```

### DELETE /stream/cache

Clear all stream cache.

**Response:** `200 OK`
```json
{
  "deleted": 100
}
```

### GET /stream/cache/info/{video_id}

Check if URL is cached.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK`
```json
{
  "cached": true,
  "expires_at": "2026-03-27T18:00:00Z"
}
```

### DELETE /stream/cache/{video_id}

Delete cached URL.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK`

### GET /stream/status/{video_id}

Check if URL is cached (alias for `/stream/cache/info/{video_id}`).

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `video_id` | string | path | Video ID |

**Response:** `200 OK`
```json
{
  "cached": true
}
```

---

## Watch

### GET /watch/

Watch playlist (radio mode).

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `playlist_id` | string | query | Playlist ID |
| `video_id` | string | query | Start video ID |
| `limit` | integer | query | Max videos (default: 50) |

**Response:** `200 OK`
```json
{
  "playlist": {...},
  "videos": [...]
}
```

---

## Playlists

### GET /playlists/{playlist_id}

Get playlist information.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `playlist_id` | string | path | Playlist ID |
| `include_stream_urls` | boolean | query | Include stream URLs |

**Response:** `200 OK`
```json
{
  "id": "PL...",
  "title": "Playlist Title",
  "tracks": [...]
}
```

---

## Podcasts

### GET /podcasts/channel/{channel_id}

Get podcast channel.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `channel_id` | string | path | Channel ID |

**Response:** `200 OK`
```json
{
  "channel": {...}
}
```

### GET /podcasts/channel/{channel_id}/episodes

Get channel episodes.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `channel_id` | string | path | Channel ID |

**Response:** `200 OK`
```json
{
  "episodes": [...]
}
```

### GET /podcasts/{browse_id}

Get podcast.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `browse_id` | string | path | Browse ID |

**Response:** `200 OK`
```json
{
  "podcast": {...}
}
```

### GET /podcasts/episode/{browse_id}

Get episode.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `browse_id` | string | path | Browse ID |

**Response:** `200 OK`
```json
{
  "episode": {...}
}
```

### GET /podcasts/episodes/{browse_id}/playlist

Get episodes playlist.

**Parameters:**
| Name | Type | In | Description |
|------|------|-----|-------------|
| `browse_id` | string | path | Browse ID |

**Response:** `200 OK`
```json
{
  "playlist": {...}
}
```

---

## Auth

### POST /auth/credentials

Save OAuth credentials.

**Headers:** `X-Admin-Key` (required)

**Request Body:**
```json
{
  "client_id": "xxx.apps.googleusercontent.com",
  "client_secret": "xxx"
}
```

**Response:** `200 OK`
```json
{
  "has_credentials": true,
  "updated_at": "2026-03-27T16:00:00Z"
}
```

### GET /auth/credentials

Check credentials status.

**Headers:** `X-Admin-Key` (required)

**Response:** `200 OK`
```json
{
  "has_credentials": true,
  "updated_at": "2026-03-27T16:00:00Z"
}
```

### POST /auth/oauth/start

Start OAuth flow.

**Headers:** `X-Admin-Key` (required)

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "verification_url": "https://www.google.com/device",
  "user_code": "ABCD-EFGH",
  "expires_in": 900,
  "interval": 5
}
```

### POST /auth/oauth/poll

Poll OAuth authorization.

**Headers:** `X-Admin-Key` (required)

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK` (pending)
```json
{
  "status": "pending",
  "message": "Waiting for user authorization"
}
```

**Response:** `200 OK` (authorized)
```json
{
  "status": "authorized",
  "message": "OAuth token saved successfully"
}
```

### GET /auth/status

Get authentication status.

**Headers:** `X-Admin-Key` (required)

**Response:** `200 OK`
```json
{
  "authenticated": true,
  "has_credentials": true,
  "has_token": true,
  "method": "oauth"
}
```

---

## Stats

### GET /stats/stats

Get service statistics.

**Response:** `200 OK`
```json
{
  "service": "YouTube Music API",
  "version": "1.0.0",
  "status": "healthy",
  "uptime_seconds": 3600,
  "cache": {
    "enabled": true,
    "backend": "redis",
    "keys": 150
  },
  "rate_limiting": {
    "enabled": true,
    "requests_per_minute": 60
  }
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": true,
  "error_code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_ERROR` | 401 | YouTube authentication failed |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_ERROR` | 429 | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | 502 | External service (YouTube) error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

- **Limit:** 60 requests per minute per IP
- **Enabled by default** via `RATE_LIMIT_ENABLED`
- Can be disabled via environment variable

---

## Caching

| Type | TTL | Description |
|------|-----|-------------|
| Metadata | 1-24 hours | Songs, albums, playlists |
| Stream URLs | 1 hour | Direct audio URLs |

Stream URLs are fetched at runtime to avoid 403 errors from expired URLs.

---

## OpenAPI Specification

The full OpenAPI specification is available at:
- JSON: `/openapi.json`
- YAML: `/openapi.yaml`

---

## Recent Fixes

| Ticket | Endpoint | Issue | Fix |
|--------|----------|-------|-----|
| SCRUM-32 | `/browse/album/{id}/browse-id` | 500 when ytmusicapi returns None | Fallback to `get_album` to extract `audioPlaylistId` |
| SCRUM-33 | `/stats/stats` | 500 due to ImportError if Redis unavailable | Graceful degradation with informative error |
| SCRUM-34 | `/explore/category/{params}` | ytmusicapi deprecated | Alias to `/explore/moods/{params}` with `Warning: 299` header |
| SCRUM-35 | `/browse/artist/{id}/albums` | 500 due to rate limit (429) | Retry (2 attempts) + fallback via `get_artist()` |
