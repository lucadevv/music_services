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
)
from app.schemas.browse import (
    ArtistResponse,
    ArtistAlbumsResponse,
    AlbumResponse,
    SongResponse,
    LyricsResponse,
    HomeResponse,
)
from app.schemas.stream import (
    StreamUrlResponse,
    StreamEnrichedItem,
    StreamBatchResponse,
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
)
from app.schemas.watch import (
    WatchPlaylistResponse,
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
    # Browse
    "ArtistResponse",
    "ArtistAlbumsResponse",
    "AlbumResponse",
    "SongResponse",
    "LyricsResponse",
    "HomeResponse",
    # Stream
    "StreamUrlResponse",
    "StreamEnrichedItem",
    "StreamBatchResponse",
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
    # Watch
    "WatchPlaylistResponse",
    # Errors
    "ErrorResponse",
    "ErrorDetailItem",
    "ErrorDetails",
    "COMMON_ERROR_RESPONSES",
]
