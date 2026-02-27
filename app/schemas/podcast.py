"""Podcast schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PodcastEpisode(BaseModel):
    """A podcast episode."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Episode title")
    description: Optional[str] = Field(None, description="Episode description")
    duration: Optional[str] = Field(None, description="Duration text")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    published_at: Optional[str] = Field(None, description="Publication date")
    
    class Config:
        extra = "allow"


class PodcastChannelResponse(BaseModel):
    """Response for podcast channel endpoint."""
    
    title: Optional[str] = Field(None, description="Channel title")
    channel_id: Optional[str] = Field(None, description="Channel ID")
    description: Optional[str] = Field(None, description="Channel description")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Channel thumbnails")
    episodes: Optional[List[PodcastEpisode]] = Field(None, description="List of episodes")
    
    class Config:
        extra = "allow"


class PodcastEpisodeResponse(BaseModel):
    """Response for podcast episode endpoint."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Episode title")
    description: Optional[str] = Field(None, description="Episode description")
    duration: Optional[str] = Field(None, description="Duration text")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    published_at: Optional[str] = Field(None, description="Publication date")
    podcast: Optional[Dict[str, Any]] = Field(None, description="Parent podcast info")
    
    class Config:
        extra = "allow"


class PodcastResponse(BaseModel):
    """Response for podcast endpoint."""
    
    id: Optional[str] = Field(None, description="Podcast ID")
    title: Optional[str] = Field(None, description="Podcast title")
    description: Optional[str] = Field(None, description="Podcast description")
    author: Optional[str] = Field(None, description="Podcast author")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Podcast thumbnails")
    episodes: Optional[List[PodcastEpisode]] = Field(None, description="List of episodes")
    
    class Config:
        extra = "allow"
