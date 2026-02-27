"""Explore schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MoodCategory(BaseModel):
    """A mood or genre category."""
    
    title: Optional[str] = Field(None, description="Category title/name")
    params: Optional[str] = Field(None, description="Params to use for fetching playlists")
    color: Optional[str] = Field(None, description="Background color")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Category thumbnails")
    
    class Config:
        extra = "allow"


class MoodCategoriesResponse(BaseModel):
    """Response for mood categories endpoint."""
    
    categories: Dict[str, List[MoodCategory]] = Field(
        ..., 
        description="Categories organized by section (For you, Genres, Moods & moments)"
    )
    structure: Optional[str] = Field(
        None, 
        description="Description of the structure"
    )


class ChartsTrack(BaseModel):
    """A track in charts."""
    
    video_id: Optional[str] = Field(None, description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: Optional[List[Dict[str, Any]]] = Field(None, description="List of artists")
    album: Optional[Dict[str, Any]] = Field(None, description="Album information")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, description="Direct audio stream URL")
    rank: Optional[int] = Field(None, description="Chart position")
    views: Optional[str] = Field(None, description="View count")
    
    class Config:
        extra = "allow"


class ChartsResponse(BaseModel):
    """Response for charts endpoint."""
    
    top_songs: Optional[List[ChartsTrack]] = Field(None, description="Top songs chart")
    trending: Optional[List[ChartsTrack]] = Field(None, description="Trending songs")
    country: Optional[str] = Field(None, description="Country code or 'global'")


class ExploreResponse(BaseModel):
    """Response for explore endpoint."""
    
    moods_genres: List[MoodCategory] = Field(..., description="Mood and genre categories")
    home: List[Dict[str, Any]] = Field(default_factory=list, description="Home page content")
    charts: ChartsResponse = Field(..., description="Music charts")
    info: Optional[Dict[str, str]] = Field(None, description="Usage information")


class MoodPlaylist(BaseModel):
    """A playlist in a mood/genre category."""
    
    playlist_id: Optional[str] = Field(None, description="Playlist ID")
    title: Optional[str] = Field(None, description="Playlist title")
    description: Optional[str] = Field(None, description="Playlist description")
    thumbnails: Optional[List[Dict[str, Any]]] = Field(None, description="Playlist thumbnails")
    count: Optional[int] = Field(None, description="Number of tracks")
    author: Optional[Dict[str, Any]] = Field(None, description="Playlist author")
    
    class Config:
        extra = "allow"


class MoodPlaylistsResponse(BaseModel):
    """Response for mood playlists endpoint."""
    
    playlists: List[MoodPlaylist] = Field(..., description="List of playlists")
    method: Optional[str] = Field(None, description="Method used: direct, search, alternative_search")
    genre_name: Optional[str] = Field(None, description="Genre name used for search")
    message: Optional[str] = Field(None, description="Additional information")
