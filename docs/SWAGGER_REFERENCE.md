# Swagger Reference (Endpoints + Schemas)

This document is a quick human-readable reference for the generated Swagger/OpenAPI spec in `openapi.json`.

## Source of truth

- JSON spec: `openapi.json`
- Interactive docs: `/docs`
- Alternative docs: `/redoc`

## Authentication model

- Music endpoints (`/search`, `/browse`, `/explore`, `/playlists`, `/watch`, `/stream`, `/podcasts`) require:
  - `Authorization: Bearer <api_key>`
- Admin endpoints (`/auth/*`, `/api-keys/*`, `/stats/*`) require:
  - `X-Admin-Key: <ADMIN_SECRET_KEY>`

## Endpoint inventory

### General
- `GET /`
- `GET /health`

### API Keys (Admin)
- `POST /api/v1/api-keys/`
- `GET /api/v1/api-keys/`
- `GET /api/v1/api-keys/{key_id}`
- `PATCH /api/v1/api-keys/{key_id}`
- `DELETE /api/v1/api-keys/{key_id}`
- `POST /api/v1/api-keys/verify`

### Auth (Admin)
- `POST /api/v1/auth/browser/from-url`
- `POST /api/v1/auth/browser/from-headers`
- `GET /api/v1/auth/browser`
- `DELETE /api/v1/auth/browser/{account_name}`
- `POST /api/v1/auth/browser/test`
- `GET /api/v1/auth/status`
- `POST /api/v1/auth/api-keys`
- `GET /api/v1/auth/api-keys`
- `GET /api/v1/auth/api-keys/{key_id}`
- `PATCH /api/v1/auth/api-keys/{key_id}`
- `DELETE /api/v1/auth/api-keys/{key_id}`
- `POST /api/v1/auth/api-keys/verify`

### Browse
- `GET /api/v1/browse/home`
- `GET /api/v1/browse/artist/{channel_id}/albums`
- `GET /api/v1/browse/album/{album_id}`
- `GET /api/v1/browse/album/{album_id}/browse-id`
- `GET /api/v1/browse/song/{video_id}`
- `GET /api/v1/browse/song/{video_id}/related`
- `GET /api/v1/browse/lyrics/{browse_id}`
- `GET /api/v1/browse/lyrics-by-video/{video_id}`

### Explore
- `GET /api/v1/explore/`
- `GET /api/v1/explore/charts`
- `GET /api/v1/explore/moods`
- `GET /api/v1/explore/moods/{params}`
- `GET /api/v1/explore/category/{category_params}`

### Search
- `GET /api/v1/search/`
- `GET /api/v1/search/suggestions`
- `DELETE /api/v1/search/suggestions`

### Playlists
- `GET /api/v1/playlists/{playlist_id}`

### Watch
- `GET /api/v1/watch/`

### Stream
- `GET /api/v1/stream/{video_id}`
- `POST /api/v1/stream/batch`
- `GET /api/v1/stream/status/{video_id}`
- `GET /api/v1/stream/proxy/{video_id}`
- `GET /api/v1/stream/cache/stats`
- `DELETE /api/v1/stream/cache`
- `GET /api/v1/stream/cache`
- `GET /api/v1/stream/cache/info/{video_id}`
- `DELETE /api/v1/stream/cache/{video_id}`

### Podcasts
- `GET /api/v1/podcasts/{browse_id}`
- `GET /api/v1/podcasts/episode/{browse_id}`
- `GET /api/v1/podcasts/channel/{channel_id}`
- `GET /api/v1/podcasts/channel/{channel_id}/episodes`
- `GET /api/v1/podcasts/episodes/{browse_id}/playlist`

### Stats (Admin)
- `GET /api/v1/stats/stats`

## Schema inventory (`components.schemas`)

- `APIKeyCreate`
- `APIKeyListResponse`
- `APIKeyResponse`
- `APIKeyUpdate`
- `APIKeyVerifyResponse`
- `AlbumBrowseIdResponse`
- `AlbumResponse`
- `AlbumTrack`
- `ArtistAlbumsResponse`
- `AuthStatusResponse`
- `BatchResultItem`
- `BatchSummary`
- `BrowserAccountInfo`
- `BrowserAddResponse`
- `BrowserListResponse`
- `BrowserTestResponse`
- `CacheClearResponse`
- `CacheDeleteInfo`
- `CacheDeleteResponse`
- `CacheInfoResponse`
- `CacheMetadataInfo`
- `CacheStatsResponse`
- `ChartsResponse`
- `ChartsTrack`
- `ErrorDetailItem`
- `ErrorDetails`
- `ErrorResponse`
- `ExploreResponse`
- `HTTPValidationError`
- `HomeResponse`
- `LyricsResponse`
- `MoodCategoriesResponse`
- `MoodCategory`
- `MoodPlaylist`
- `MoodPlaylistsResponse`
- `PlaylistResponse`
- `PlaylistTrack`
- `PodcastChannelResponse`
- `PodcastEpisode`
- `PodcastEpisodeResponse`
- `PodcastResponse`
- `RelatedSongItem`
- `RelatedSongsResponse`
- `SearchResponse`
- `SearchResult`
- `SearchSuggestionsResponse`
- `SongResponse`
- `StatsResponse`
- `StreamBatchResponse`
- `StreamCacheStatusResponse`
- `StreamUrlResponse`
- `SuccessResponse`
- `ValidationError`
- `WatchPlaylistResponse`
- `WatchTrack`

## How to refresh these docs

From project root:

```bash
curl -sS http://localhost:8000/openapi.json -o openapi.json
```

Then update this Markdown if new paths or schemas are added.
