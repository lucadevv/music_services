"""Watch playlist schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

from app.schemas.common import Artist, Album, Thumbnail, PaginationMeta, LikeStatus


class WatchRequest(BaseModel):
    """Request parameters for watch playlist endpoint."""
    
    video_id: Optional[str] = Field(None, alias="videoId", pattern=r"^[a-zA-Z0-9_-]{11}$", description="Video ID to start from")
    playlist_id: Optional[str] = Field(None, alias="playlistId", pattern=r"^RD[A-Z0-9]+$", description="Playlist ID")
    limit: int = Field(25, ge=1, le=100, description="Max tracks from ytmusicapi")
    radio: bool = Field(False, description="Generate radio playlist")
    shuffle: bool = Field(False, description="Shuffle playlist")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=50, description="Items per page")
    
    @model_validator(mode='after')
    def require_one_source(self):
        """Either video_id or playlist_id must be provided."""
        if not self.video_id and not self.playlist_id:
            raise ValueError("video_id or playlist_id is required")
        return self


class WatchTrack(BaseModel):
    """A track in a watch playlist with normalized fields."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds (normalized from length)")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text (e.g., '3:45')")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    
    # Watch playlist specific fields
    like_status: Optional[LikeStatus] = Field(None, alias="likeStatus", description="Like status")
    in_library: Optional[bool] = Field(None, alias="inLibrary", description="In library")
    is_available: Optional[bool] = Field(None, alias="isAvailable", description="Is available")
    video_type: Optional[str] = Field(None, alias="videoType", description="Video type")
    year: Optional[str] = Field(None, description="Release year")
    set_video_id: Optional[str] = Field(None, alias="setVideoId", description="Set video ID for operations")
    pinned_to_listen_again: Optional[bool] = Field(None, alias="pinnedToListenAgain", description="Pinned to Listen Again")
    feedback_tokens: Optional[Dict[str, str]] = Field(None, alias="feedbackTokens", description="Feedback tokens")


class WatchPlaylistResponse(BaseModel):
    """Response for watch playlist endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    watch_playlist_metadata: Optional[Dict[str, Any]] = Field(None, alias="watchPlaylistMetadata", description="Playlist metadata")
    tracks: List[WatchTrack] = Field(default_factory=list, alias="items", description="List of tracks (normalized)")
    items: Optional[List[WatchTrack]] = Field(None, description="Alternative list of tracks")
    playlist_id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")
    lyrics: Optional[str] = Field(None, description="Lyrics browse ID")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    stream_urls_prefetched: Optional[int] = Field(None, alias="streamUrlsPrefetched", description="Tracks with prefetched URLs")
    stream_urls_total: Optional[int] = Field(None, alias="streamUrlsTotal", description="Total tracks")