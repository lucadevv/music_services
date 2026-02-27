"""Playlist schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlaylistTrack(BaseModel):
    """A track in a playlist."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    duration: Optional[str] = Field(None, description="Duration text")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    set_video_id: Optional[str] = Field(None, description="Set video ID for playlist operations")
    
    class Config:
        extra = "allow"


class PlaylistResponse(BaseModel):
    """Response for playlist endpoint."""
    
    id: Optional[str] = Field(None, description="Playlist ID")
    title: Optional[str] = Field(None, description="Playlist title")
    description: Optional[str] = Field(None, description="Playlist description")
    author: Optional[Dict[str, Any]] = Field(None, description="Playlist author")
    track_count: Optional[int] = Field(None, description="Number of tracks")
    duration: Optional[str] = Field(None, description="Total duration")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Playlist thumbnails")
    tracks: Optional[List[PlaylistTrack]] = Field(None, description="List of tracks")
    views: Optional[str] = Field(None, description="View count")
    year: Optional[str] = Field(None, description="Year created")
    privacy: Optional[str] = Field(None, description="Privacy status")
    
    class Config:
        extra = "allow"
