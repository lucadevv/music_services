"""Browse schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import (
    Artist, Album, Thumbnail, PaginationMeta, LikeStatus
)


class HomeResponse(BaseModel):
    """Response for home endpoint."""
    
    model_config = ConfigDict(extra="allow")


class ArtistResponse(BaseModel):
    """Response for artist endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    description: Optional[str] = Field(None, description="Artist description")
    name: Optional[str] = Field(None, description="Artist name")
    channel_id: Optional[str] = Field(None, alias="channelId", description="Channel ID")
    views: Optional[str] = Field(None, description="View count")
    subscribers: Optional[str] = Field(None, description="Subscriber count")
    monthly_listeners: Optional[str] = Field(None, alias="monthlyListeners", description="Monthly listeners")
    subscribed: Optional[bool] = Field(None, description="Is user subscribed")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Artist thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")
    songs: Optional[Dict[str, Any]] = Field(None, description="Top songs")
    albums: Optional[Dict[str, Any]] = Field(None, description="Albums")
    singles: Optional[Dict[str, Any]] = Field(None, description="Singles")
    videos: Optional[Dict[str, Any]] = Field(None, description="Videos")
    related: Optional[List[Dict[str, Any]]] = Field(None, description="Related artists")


class ArtistAlbumItem(BaseModel):
    """A single album in artist albums list."""
    
    model_config = ConfigDict(extra="allow")
    
    title: str = Field(..., description="Album title")
    type: Optional[str] = Field(None, description="Album type: Album, Single, EP")
    year: Optional[str] = Field(None, description="Release year")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID")
    audio_playlist_id: Optional[str] = Field(None, alias="audioPlaylistId", description="Audio playlist ID")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit flag")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Album thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")


class ArtistAlbumsResponse(BaseModel):
    """Response for artist albums endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    results: List[ArtistAlbumItem] = Field(default_factory=list, description="List of albums")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID for pagination")
    next_page_token: Optional[str] = Field(None, alias="params", description="Token for next page")


class AlbumTrack(BaseModel):
    """A track in an album with normalized duration."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    title: Optional[str] = Field(None, description="Track title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[str] = Field(None, description="Album name (string, not object)")
    duration: Optional[int] = Field(None, description="Duration in seconds (normalized)")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text (e.g., '3:45')")
    track_number: Optional[int] = Field(None, alias="trackNumber", description="Track number")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit flag")
    is_available: Optional[bool] = Field(None, alias="isAvailable", description="Is available")
    in_library: Optional[bool] = Field(None, alias="inLibrary", description="In library")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    like_status: Optional[LikeStatus] = Field(None, alias="likeStatus", description="Like status")


class AlbumResponse(BaseModel):
    """Response for album endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    title: Optional[str] = Field(None, description="Album title")
    description: Optional[str] = Field(None, description="Album description")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    year: Optional[str] = Field(None, description="Release year")
    track_count: Optional[int] = Field(None, alias="trackCount", description="Number of tracks")
    duration: Optional[str] = Field(None, description="Total duration as text")
    duration_seconds: Optional[int] = Field(None, alias="durationSeconds", description="Total duration in seconds")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Album thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")
    tracks: List[AlbumTrack] = Field(default_factory=list, description="List of tracks")
    audio_playlist_id: Optional[str] = Field(None, alias="audioPlaylistId", description="Audio playlist ID")
    other_versions: Optional[List[Dict[str, Any]]] = Field(None, alias="otherVersions", description="Other versions")


class SongResponse(BaseModel):
    """Response for song endpoint (normalized from yt.get_song())."""
    
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    video_id: str = Field(..., alias="videoId", description="Video ID")
    title: str = Field(..., description="Song title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit flag")
    playability_status: Optional[str] = Field(None, alias="playabilityStatus", description="Playability status")
    video_type: Optional[str] = Field(None, alias="videoType", description="Video type")
    keywords: Optional[List[str]] = Field(None, description="Video keywords")
    short_description: Optional[str] = Field(None, alias="shortDescription", description="Short description")
    view_count: Optional[str] = Field(None, alias="viewCount", description="View count")


class LyricsResponse(BaseModel):
    """Response for lyrics endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    lyrics: Optional[str] = Field(None, description="Song lyrics")
    source: Optional[str] = Field(None, description="Lyrics source")
    has_timestamps: Optional[bool] = Field(None, alias="hasTimestamps", description="Has timestamps")


class AlbumBrowseIdResponse(BaseModel):
    """Response for album browse ID endpoint."""
    
    browse_id: str = Field(..., alias="browseId", description="Album browse ID")


class RelatedSongItem(BaseModel):
    """A related song item with normalized fields."""
    
    model_config = ConfigDict(extra="allow")
    
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    title: Optional[str] = Field(None, description="Song title")
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds (normalized)")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")


class RelatedSongsResponse(BaseModel):
    """Response for related songs endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    songs: List[RelatedSongItem] = Field(default_factory=list, alias="items", description="List of related songs")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    total_results: Optional[int] = Field(None, alias="totalResults", description="Total number of songs")


class MoodCategory(BaseModel):
    """A mood/genre category."""
    
    title: str = Field(..., description="Category title")
    params: Optional[str] = Field(None, description="Base64 params for get_mood_playlists")


class MoodCategoriesResponse(BaseModel):
    """Response for mood categories endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    categories: Dict[str, List[MoodCategory]] = Field(default_factory=dict, description="Mood categories by section")


class MoodPlaylistItem(BaseModel):
    """A playlist in mood/genre."""
    
    model_config = ConfigDict(extra="allow")
    
    title: str = Field(..., description="Playlist title")
    playlist_id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")
    description: Optional[str] = Field(None, description="Playlist description")
    author: Optional[List[Dict[str, Any]]] = Field(None, description="Author info")
    count: Optional[str] = Field(None, description="Track count")


class ChartItem(BaseModel):
    """A chart item (artist or video)."""
    
    model_config = ConfigDict(extra="allow")
    
    title: str = Field(..., description="Title")
    rank: Optional[int] = Field(None, description="Rank position")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID")
    video_id: Optional[str] = Field(None, alias="videoId", description="Video ID")
    playlist_id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="Thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail")
    subscribers: Optional[str] = Field(None, description="Subscriber count")
    trend: Optional[str] = Field(None, description="Trend (up, down, same)")


class ChartsResponse(BaseModel):
    """Response for charts endpoint."""
    
    model_config = ConfigDict(extra="allow")
    
    countries: Optional[Dict[str, Any]] = Field(None, description="Country selection info")
    videos: List[ChartItem] = Field(default_factory=list, description="Trending videos")
    artists: List[ChartItem] = Field(default_factory=list, description="Trending artists")
    genres: List[Dict[str, Any]] = Field(default_factory=list, description="Popular genres")