"""Search schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result item."""
    
    video_id: Optional[str] = Field(None, description="YouTube video ID (for songs/videos)")
    playlist_id: Optional[str] = Field(None, description="Playlist ID")
    browse_id: Optional[str] = Field(None, description="Browse ID (for artists/albums)")
    title: str = Field(..., description="Title of the result")
    result_type: Optional[str] = Field(None, description="Type: song, video, album, artist, playlist")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    duration: Optional[str] = Field(None, description="Duration text")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="List of thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    views: Optional[str] = Field(None, description="View count")
    subscribers: Optional[str] = Field(None, description="Subscriber count (for channels)")
    
    class Config:
        extra = "allow"  # Allow additional fields from ytmusicapi


class SearchResponse(BaseModel):
    """Response for search endpoint."""
    
    results: List[SearchResult] = Field(..., description="List of search results")
    query: str = Field(..., description="Original search query")


class SearchSuggestionsResponse(BaseModel):
    """Response for search suggestions endpoint."""
    
    suggestions: List[str] = Field(..., description="List of search suggestions")
