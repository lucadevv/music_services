"""Pydantic schemas for API responses."""
from app.schemas.common import (
    Thumbnail,
    Artist,
    Album,
    SongBasic,
    StreamingInfo,
    ErrorResponse,
    SuccessResponse,
    PaginationMeta,
    LikeStatus,
    PrivacyStatus,
    VideoType,
    SearchFilter,
)

# Backwards compatibility aliases
ArtistBasic = Artist
AlbumBasic = Album
from app.schemas.search import (
    SearchResultItem,
    SearchResponse,
    SearchRequest,
    SearchSuggestionsResponse,
    SearchSuggestionsDetailedResponse,
    RemoveSuggestionRequest,
    RemoveSearchSuggestionsRequest,
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
    AlbumTrack,
    MoodCategory,
    MoodCategoriesResponse,
    ChartsResponse,
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
    MoodPlaylistsPaginatedResponse,
)
from app.schemas.playlist import (
    PlaylistTrack,
    PlaylistResponse,
    PlaylistCreateRequest,
    PlaylistEditRequest,
)
from app.schemas.watch import (
    WatchPlaylistResponse,
    WatchTrack,
    WatchRequest,
)
from app.schemas.errors import (
    ErrorResponse as ErrorResponseSchema,
    ErrorDetailItem,
    ErrorDetails,
    COMMON_ERROR_RESPONSES,
)

# Re-export for backwards compatibility
ArtistBasic = Artist
AlbumBasic = Album

__all__ = [
    # Common
    "Thumbnail",
    "Artist",
    "Album",
    "SongBasic",
    "StreamingInfo",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationMeta",
    "LikeStatus",
    "PrivacyStatus",
    "VideoType",
    "SearchFilter",
    # Backwards
    "ArtistBasic",
    "AlbumBasic",
    # Search
    "SearchResultItem",
    "SearchResponse",
    "SearchRequest",
    "SearchSuggestionsResponse",
    "SearchSuggestionsDetailedResponse",
    "RemoveSuggestionRequest",
    "RemoveSearchSuggestionsRequest",
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
    "AlbumTrack",
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
    "MoodPlaylistsPaginatedResponse",
    # Playlist
    "PlaylistTrack",
    "PlaylistResponse",
    "PlaylistCreateRequest",
    "PlaylistEditRequest",
    # Podcast
    "PodcastChannelResponse",
    "PodcastEpisodeResponse",
    "PodcastResponse",
    "PodcastEpisode",
    # Watch
    "WatchPlaylistResponse",
    "WatchTrack",
    "WatchRequest",
    # Errors
    "ErrorResponseSchema",
    "ErrorDetailItem",
    "ErrorDetails",
    "COMMON_ERROR_RESPONSES",
]