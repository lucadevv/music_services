"""Browse schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HomeResponse(BaseModel):
    """Response for home endpoint."""
    
    # Home content is a list of sections, each with title and contents
    # The structure is dynamic, so we use Any for flexibility
    
    class Config:
        extra = "allow"


class ArtistResponse(BaseModel):
    """Response for artist endpoint."""
    
    description: Optional[str] = Field(None, description="Artist description")
    name: Optional[str] = Field(None, description="Artist name")
    channel_id: Optional[str] = Field(None, description="Channel ID")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Artist thumbnails")
    views: Optional[str] = Field(None, description="View count")
    subscribers: Optional[str] = Field(None, description="Subscriber count")
    top_releases: Optional[Dict[str, Any]] = Field(None, description="Top releases")
    related: Optional[List[Dict[str, Any]]] = Field(None, description="Related artists")
    
    class Config:
        extra = "allow"


class ArtistAlbumsResponse(BaseModel):
    """Response for artist albums endpoint."""
    
    results: Optional[List[Dict[str, Any]]] = Field(None, description="List of albums")
    browse_id: Optional[str] = Field(None, description="Browse ID")
    
    class Config:
        extra = "allow"


class AlbumTrack(BaseModel):
    """A track in an album."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    duration: Optional[str] = Field(None, description="Duration")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    
    class Config:
        extra = "allow"


class AlbumResponse(BaseModel):
    """Response for album endpoint."""
    
    title: Optional[str] = Field(None, description="Album title")
    description: Optional[str] = Field(None, description="Album description")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    year: Optional[str] = Field(None, description="Release year")
    track_count: Optional[int] = Field(None, description="Number of tracks")
    duration: Optional[str] = Field(None, description="Total duration")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Album thumbnails")
    tracks: Optional[List[AlbumTrack]] = Field(None, description="List of tracks")
    audio_playlist_id: Optional[str] = Field(None, description="Audio playlist ID")
    
    class Config:
        extra = "allow"


class SongResponse(BaseModel):
    """Response for song endpoint."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Song title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    duration: Optional[str] = Field(None, description="Duration")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    
    class Config:
        extra = "allow"


class LyricsResponse(BaseModel):
    """Response for lyrics endpoint."""
    
    lyrics: Optional[str] = Field(None, description="Song lyrics")
    source: Optional[str] = Field(None, description="Lyrics source")
    
    class Config:
        extra = "allow"
