"""Stream schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StreamUrlResponse(BaseModel):
    """Response for stream URL endpoint."""
    
    url: str = Field(..., description="Direct audio stream URL")
    title: Optional[str] = Field(None, description="Song title")
    artist: Optional[str] = Field(None, description="Artist name")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")


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


class StreamBatchResponse(BaseModel):
    """Response for batch stream URL requests."""
    
    items: List[StreamEnrichedItem] = Field(..., description="List of enriched items")
    total: int = Field(..., description="Total number of items processed")
