"""Stream schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StreamUrlResponse(BaseModel):
    """Response for stream URL endpoint."""
    
    streamUrl: str = Field(..., description="Direct audio stream URL")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    from_cache: Optional[bool] = Field(None, description="Whether the URL was served from cache")


class StreamEnrichedItem(BaseModel):
    """An item enriched with stream URL and best thumbnail."""
    
    video_id: Optional[str] = Field(None, description="YouTube video ID")
    title: Optional[str] = Field(None, description="Item title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    duration: Optional[str] = Field(None, description="Duration text")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="List of thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    
    class Config:
        extra = "allow"


class BatchSummary(BaseModel):
    """Summary of batch stream URL request."""
    
    total: int = Field(..., description="Total number of items processed")
    cached: int = Field(..., description="Number of items served from cache")
    fetched: int = Field(..., description="Number of items freshly fetched")
    failed: int = Field(0, description="Number of items that failed")


class BatchResultItem(BaseModel):
    """Single item in batch response."""
    
    videoId: Optional[str] = Field(None, description="YouTube video ID")
    url: Optional[str] = Field(None, description="Direct audio stream URL")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[Any] = Field(None, description="Duration")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    cached: bool = Field(False, description="Whether the URL was served from cache")
    error: Optional[str] = Field(None, description="Error message if URL could not be obtained")
    
    class Config:
        extra = "allow"


class StreamBatchResponse(BaseModel):
    """Response for batch stream URL requests."""
    
    results: List[BatchResultItem] = Field(..., description="List of results with stream URLs")
    summary: BatchSummary = Field(..., description="Batch processing summary")
    
    class Config:
        extra = "allow"
