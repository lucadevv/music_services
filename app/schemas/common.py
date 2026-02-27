"""Common schemas shared across multiple endpoints."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Thumbnail(BaseModel):
    """Thumbnail image with dimensions."""
    
    url: str = Field(..., description="URL of the thumbnail image")
    width: Optional[int] = Field(None, description="Width in pixels")
    height: Optional[int] = Field(None, description="Height in pixels")


class ArtistBasic(BaseModel):
    """Basic artist information."""
    
    name: str = Field(..., description="Artist name")
    id: Optional[str] = Field(None, description="Artist channel ID")
    browse_id: Optional[str] = Field(None, description="Browse ID for navigation")


class AlbumBasic(BaseModel):
    """Basic album information."""
    
    name: str = Field(..., description="Album name")
    id: Optional[str] = Field(None, description="Album ID")
    browse_id: Optional[str] = Field(None, description="Browse ID for navigation")


class SongBasic(BaseModel):
    """Basic song information."""
    
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Song title")
    artists: List[ArtistBasic] = Field(default_factory=list, description="List of artists")
    album: Optional[AlbumBasic] = Field(None, description="Album information")
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
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response."""
    
    success: bool = Field(True, description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")
