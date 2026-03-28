"""Pydantic schemas for API responses."""
from app.schemas.common import (
    Thumbnail,
    ArtistBasic,
    AlbumBasic,
    SongBasic,
    StreamingInfo,
)
from app.schemas.search import (
    SearchResult,
    SearchResponse,
    SearchSuggestionsResponse,
    RemoveSuggestionRequest,
)
from app.schemas.browse import (
    ArtistResponse,
    ArtistAlbumsResponse,
    AlbumResponse,
    SongResponse,
    LyricsResponse,
    HomeResponse,
    AlbumBrowseIdResponse,
    RelatedSongsResponse,
    RelatedSongItem,
)
from app.schemas.stream import (
    StreamUrlResponse,
    StreamEnrichedItem,
    StreamBatchResponse,
)
from app.schemas.stream_management import (
    CacheStatsResponse,
    CacheClearResponse,
    CacheInfoResponse,
    CacheDeleteResponse,
    StreamCacheStatusResponse,
)
from app.schemas.stats import (
    StatsResponse,
    RateLimitingStats,
    CachingStats,
    CacheManagerStats,
    CircuitBreakerState,
    CircuitBreakerStats,
    PerformanceStats,
)
from app.schemas.explore import (
    MoodCategory,
    MoodCategoriesResponse,
    ChartsResponse,
    ExploreResponse,
    MoodPlaylistsResponse,
)
from app.schemas.playlist import (
    PlaylistTrack,
    PlaylistResponse,
)
from app.schemas.podcast import (
    PodcastChannelResponse,
    PodcastEpisodeResponse,
    PodcastResponse,
    PodcastEpisode,
)
from app.schemas.watch import (
    WatchPlaylistResponse,
    WatchTrack,
)
from app.schemas.errors import (
    ErrorResponse,
    ErrorDetailItem,
    ErrorDetails,
    COMMON_ERROR_RESPONSES,
)

__all__ = [
    # Common
    "Thumbnail",
    "ArtistBasic",
    "AlbumBasic",
    "SongBasic",
    "StreamingInfo",
    # Search
    "SearchResult",
    "SearchResponse",
    "SearchSuggestionsResponse",
    "RemoveSuggestionRequest",
    # Browse
    "ArtistResponse",
    "ArtistAlbumsResponse",
    "AlbumResponse",
    "SongResponse",
    "LyricsResponse",
    "HomeResponse",
    "AlbumBrowseIdResponse",
    "RelatedSongsResponse",
    "RelatedSongItem",
    # Stream
    "StreamUrlResponse",
    "StreamEnrichedItem",
    "StreamBatchResponse",
    # Stream Management
    "CacheStatsResponse",
    "CacheClearResponse",
    "CacheInfoResponse",
    "CacheDeleteResponse",
    "StreamCacheStatusResponse",
    # Stats
    "StatsResponse",
    "RateLimitingStats",
    "CachingStats",
    "CacheManagerStats",
    "CircuitBreakerState",
    "CircuitBreakerStats",
    "PerformanceStats",
    # Explore
    "MoodCategory",
    "MoodCategoriesResponse",
    "ChartsResponse",
    "ExploreResponse",
    "MoodPlaylistsResponse",
    # Playlist
    "PlaylistTrack",
    "PlaylistResponse",
    # Podcast
    "PodcastChannelResponse",
    "PodcastEpisodeResponse",
    "PodcastResponse",
    "PodcastEpisode",
    # Watch
    "WatchPlaylistResponse",
    "WatchTrack",
    # Errors
    "ErrorResponse",
    "ErrorDetailItem",
    "ErrorDetails",
    "COMMON_ERROR_RESPONSES",
]
