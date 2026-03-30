"""Common schemas shared across multiple endpoints."""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.config import ConfigDict


class LikeStatus(str, Enum):
    """Like status enum from ytmusicapi."""
    INDIFFERENT = "INDIFFERENT"
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"


class PrivacyStatus(str, Enum):
    """Privacy status for playlists."""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    UNLISTED = "UNLISTED"


class VideoType(str, Enum):
    """Video type enum from ytmusicapi."""
    ATV = "ATV"
    OMV = "OMV"
    UGC = "UGC"


class SearchFilter(str, Enum):
    """Search filter types."""
    SONGS = "songs"
    VIDEOS = "videos"
    ALBUMS = "albums"
    ARTISTS = "artists"
    PLAYLISTS = "playlists"
    COMMUNITY_PLAYLISTS = "community_playlists"
    FEATURED_PLAYLISTS = "featured_playlists"
    UPLOADS = "uploads"


class Thumbnail(BaseModel):
    """Thumbnail image with dimensions."""
    
    url: str = Field(..., description="URL of the thumbnail image")
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")
    
    @property
    def best_url(self) -> str:
        """Returns the best quality URL (already ordered by ytmusicapi)."""
        return self.url


class Artist(BaseModel):
    """Artist with normalized id/browseId."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., description="Artist name")
    id: Optional[str] = Field(None, description="Artist channel ID (normalized)")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID for navigation")
    
    @model_validator(mode='after')
    def normalize_ids(self):
        """Normalize: if id is empty and browse_id exists, use browse_id."""
        if not self.id and self.browse_id:
            self.id = self.browse_id
        return self


class Album(BaseModel):
    """Album with normalized id/browseId."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(..., description="Album name")
    id: Optional[str] = Field(None, description="Album ID (normalized)")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID for navigation")
    
    @model_validator(mode='after')
    def normalize_ids(self):
        """Normalize: if id is empty and browse_id exists, use browse_id."""
        if not self.id and self.browse_id:
            self.id = self.browse_id
        return self


class SongBasic(BaseModel):
    """Basic song information."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Song title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    duration_text: Optional[str] = Field(None, description="Duration as text (e.g., '3:45')")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="List of thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")


class StreamingInfo(BaseModel):
    """Streaming URL and metadata."""
    
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    url: Optional[str] = Field(None, description="Direct audio stream URL (alias)")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: bool = Field(True, description="Error flag")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response."""
    
    success: bool = Field(True, description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")


class PaginationMeta(BaseModel):
    """Standard pagination metadata for all endpoints."""
    
    total_results: int = Field(0, description="Total number of results")
    total_pages: int = Field(0, description="Total number of pages")
    page: int = Field(1, description="Current page")
    page_size: int = Field(10, description="Items per page")
    has_next: bool = Field(False, description="Has next page")
    has_prev: bool = Field(False, description="Has previous page")
    start_index: int = Field(0, description="Start index of current page")
    end_index: int = Field(0, description="End index of current page")