"""Stream schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import Artist, Album, Thumbnail


class StreamUrlResponse(BaseModel):
    """Response for stream URL endpoint."""
    
    stream_url: str = Field(..., alias="streamUrl", description="Direct audio stream URL")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    from_cache: Optional[bool] = Field(None, alias="fromCache", description="Whether the URL was served from cache")


class StreamEnrichedItem(BaseModel):
    """An item enriched with stream URL and best thumbnail."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="YouTube video ID")
    title: Optional[str] = Field(None, description="Item title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds (normalized)")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="List of thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit flag")


class BatchSummary(BaseModel):
    """Summary of batch stream URL request."""
    
    total: int = Field(..., description="Total number of items processed")
    cached: int = Field(..., description="Number of items served from cache")
    fetched: int = Field(..., description="Number of items freshly fetched")
    failed: int = Field(0, alias="failed", description="Number of items that failed")


class BatchResultItem(BaseModel):
    """Single item in batch response."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="YouTube video ID")
    url: Optional[str] = Field(None, description="Direct audio stream URL")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    cached: bool = Field(False, description="Whether the URL was served from cache")
    error: Optional[str] = Field(None, description="Error message if URL could not be obtained")


class StreamBatchResponse(BaseModel):
    """Response for batch stream URL requests."""
    
    model_config = ConfigDict(extra="allow")
    
    results: List[BatchResultItem] = Field(..., description="List of results with stream URLs")
    summary: BatchSummary = Field(..., description="Batch processing summary")