"""Watch playlist schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class WatchTrack(BaseModel):
    """A track in a watch playlist."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    duration: Optional[str] = Field(None, description="Duration text")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    
    class Config:
        extra = "allow"


class WatchPlaylistResponse(BaseModel):
    """Response for watch playlist endpoint."""
    
    tracks: Optional[List[WatchTrack]] = Field(None, description="List of tracks")
    items: Optional[List[WatchTrack]] = Field(None, description="Alternative list of tracks")
    playlist_id: Optional[str] = Field(None, description="Playlist ID")
    lyrics: Optional[str] = Field(None, description="Lyrics browse ID")
    stream_urls_prefetched: Optional[int] = Field(None, description="Number of tracks with prefetched stream URLs")
    stream_urls_total: Optional[int] = Field(None, description="Total number of tracks")
    
    model_config = ConfigDict(extra="allow")
