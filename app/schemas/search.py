"""Search schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict

from app.schemas.common import (
    Artist, Album, Thumbnail, PaginationMeta, SearchFilter
)


class SearchRequest(BaseModel):
    """Request parameters for search endpoint."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filter: Optional[SearchFilter] = Field(None, description="Filter by type: songs, videos, albums, artists, playlists")
    scope: Optional[str] = Field(None, description="Scope: library, uploads")
    limit: int = Field(20, ge=1, le=100, description="Max results from ytmusicapi")
    ignore_spelling: bool = Field(False, description="Ignore spelling suggestions")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=50, description="Items per page")


class SearchResultItem(BaseModel):
    """A single search result item with normalized fields."""
    
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    
    video_id: Optional[str] = Field(None, alias="videoId", description="YouTube video ID (for songs/videos)")
    playlist_id: Optional[str] = Field(None, alias="playlistId", description="Playlist ID")
    browse_id: Optional[str] = Field(None, alias="browseId", description="Browse ID (for artists/albums)")
    title: str = Field(..., description="Title of the result")
    result_type: Optional[str] = Field(None, alias="resultType", description="Type: song, video, album, artist, playlist")

    @model_validator(mode="before")
    @classmethod
    def normalize_artist_title(cls, data: Any) -> Any:
        """Handle cases where ytmusicapi returns 'artist' instead of 'title' for artist results."""
        if isinstance(data, dict):
            # 1. If title is missing but artist exists, use artist as title
            if "title" not in data:
                if "artist" in data:
                    data["title"] = data["artist"]
                elif "artists" in data and isinstance(data["artists"], list) and len(data["artists"]) > 0:
                    first_artist = data["artists"][0]
                    if isinstance(first_artist, dict) and "name" in first_artist:
                        data["title"] = first_artist["name"]
                    elif hasattr(first_artist, "name"):
                        data["title"] = first_artist.name
            
            # 2. Ensure resultType is handled correctly
            if "resultType" not in data and "type" in data:
                data["resultType"] = data["type"]
        return data
    artists: List[Artist] = Field(default_factory=list, description="List of artists")
    album: Optional[Album] = Field(None, description="Album information")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    duration_text: Optional[str] = Field(None, alias="durationText", description="Duration as text (e.g., '3:45')")
    thumbnails: List[Thumbnail] = Field(default_factory=list, description="List of thumbnails")
    thumbnail: Optional[str] = Field(None, description="Best quality thumbnail URL")
    stream_url: Optional[str] = Field(None, alias="streamUrl", description="Direct audio stream URL")
    views: Optional[str] = Field(None, description="View count")
    subscribers: Optional[str] = Field(None, description="Subscriber count (for channels)")
    is_explicit: Optional[bool] = Field(None, alias="isExplicit", description="Explicit content flag")


class SearchResponse(BaseModel):
    """Response for search endpoint (matches SearchService.paginate shape)."""

    items: List[SearchResultItem] = Field(..., description="Search results")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    query: str = Field(..., description="Original query")


class SearchSuggestionsResponse(BaseModel):
    """Response for search suggestions endpoint (plain text)."""

    suggestions: List[str] = Field(..., description="Suggestions as plain text")


class SearchSuggestionsDetailedResponse(BaseModel):
    """Response when detailed_runs=True (same shape ytmusicapi returns)."""

    suggestions: List[Dict[str, Any]] = Field(
        ...,
        description="Objects returned by YTMusic.get_search_suggestions(..., detailed_runs=True)",
    )


class RemoveSearchSuggestionsRequest(BaseModel):
    """
    Eliminar sugerencias del historial (ver ytmusicapi remove_search_suggestions).

    Modo recomendado: suggestions + indices opcional (índices en esa misma lista).
    Modo compatibilidad: query = texto exacto de la sugerencia; se llama a get_search_suggestions(detailed_runs=True) y se eliminan coincidencias exactas.
    """

    suggestions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Lista devuelta por GET /search/suggestions?detailed=true",
    )
    indices: Optional[List[int]] = Field(
        None,
        description="Índices a borrar en esa lista; None = todos (comportamiento ytmusicapi)",
    )
    query: Optional[str] = Field(None, description="Texto exacto de la sugerencia a quitar (modo legado)")

    @model_validator(mode="after")
    def _one_mode(self) -> "RemoveSearchSuggestionsRequest":
        has_s = self.suggestions is not None
        has_q = bool(self.query and self.query.strip())
        if has_s and has_q:
            raise ValueError("Usa solo suggestions (+indices opcional) o solo query")
        if not has_s and not has_q:
            raise ValueError("Indica suggestions o query")
        if has_s and len(self.suggestions or []) == 0:
            raise ValueError("suggestions no puede estar vacío")
        return self


# Backwards alias
RemoveSuggestionRequest = RemoveSearchSuggestionsRequest