"""Playlist schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Artist, Album, Thumbnail, PaginationMeta, PrivacyStatus, LikeStatus


class PlaylistTrack(BaseModel):
    """A track in a playlist with normalized fields."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds (normalized)")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text (e.g., '3:45')")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    set_video_id: Optional[str] = Field(None, alias="setVideoId", description="Set video ID for operations")
    track_number: Optional[int] = Field(None, alias="trackNumber", description="Track number")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit flag")
    is_available: Optional[bool] = Field(None, alias="isAvailable", description="Is available")
    in_library: Optional[bool] = Field(None, alias="inLibrary", description="In library")
    like_status: Optional[LikeStatus] = Field(None, alias="likeStatus", description="Like status")
    pinned_to_listen_again: Optional[bool] = Field(None, alias="pinnedToListenAgain", description="Pinned to Listen Again")


class PlaylistAuthor(BaseModel):
    """Playlist author/creator."""
    
    name: str = Field(..., description="Author name")
    id: Optional[str] = Field(None, description="Author channel ID")


class PlaylistResponse(BaseModel):
    """Response for playlist endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")
    title: Optional[str] = Field(None, description="Playlist title")
    description: Optional[str] = Field(None, description="Playlist description")
    author: Optional[PlaylistAuthor] = Field(None, description="Playlist author")
    track_count: Optional[int] = Field(None, alias="trackCount", description="Number of tracks")
    duration: Optional[str] = Field(None, description="Total duration as text")
    duration_seconds: Optional[int] = Field(None, alias="durationSeconds", description="Total duration in seconds")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Playlist thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")
    tracks: List[PlaylistTrack] = Field(default_factory=list, description="List of tracks")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    views: Optional[Any] = Field(None, description="View count")
    year: Optional[Any] = Field(None, description="Year created")
    privacy: Optional[PrivacyStatus] = Field(None, description="Privacy status")
    related: Optional[List[Dict[str, Any]]] = Field(None, description="Related playlists")
    suggestions: Optional[List[Dict[str, Any]]] = Field(None, description="Suggested tracks")
    stream_urls_prefetched: Optional[int] = Field(None, alias="streamUrlsPrefetched", description="Tracks with prefetched URLs")
    stream_urls_total: Optional[int] = Field(None, alias="streamUrlsTotal", description="Total tracks")


class PlaylistCreateRequest(BaseModel):
    """Request to create a playlist."""
    
    title: str = Field(..., min_length=1, max_length=200, description="Playlist title")
    description: Optional[str] = Field("", max_length=1000, description="Playlist description")
    privacy_status: PrivacyStatus = Field(PrivacyStatus.PRIVATE, alias="privacyStatus", description="Privacy status")
    video_ids: Optional[List[str]] = Field(None, alias="videoIds", description="Initial video IDs")
    source_playlist: Optional[str] = Field(None, alias="sourcePlaylist", description="Source playlist to copy")


class PlaylistEditRequest(BaseModel):
    """Request to edit a playlist."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New title")
    description: Optional[str] = Field(None, max_length=1000, description="New description")
    privacy_status: Optional[PrivacyStatus] = Field(None, alias="privacyStatus", description="New privacy status")
    move_item: Optional[str] = Field(None, alias="moveItem", description="setVideoId to move")
    add_playlist_id: Optional[str] = Field(None, alias="addPlaylistId", description="Playlist to add from")
    add_to_top: Optional[bool] = Field(None, alias="addToTop", description="Add to top")