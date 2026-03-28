"""Service for standardizing API responses."""
from typing import Any, Dict, Optional, List
import datetime


class ResponseService:
    """Service for creating standardized API responses."""

    @staticmethod
    def create_paginated_response(
        items: List[Any],
        pagination: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized paginated response.

        Args:
            items: List of items
            pagination: Pagination metadata (from PaginationService.paginate)
            extra_data: Optional additional data

        Returns:
            Standardized response dict
        """
        response = {
            "items": items,
            "pagination": pagination,
            "metadata": {
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "version": "1.0"
            }
        }

        if extra_data:
            response.update(extra_data)

        return response

    @staticmethod
    def standardize_song_object(
        song: Dict[str, Any],
        include_stream_url: bool = False
    ) -> Dict[str, Any]:
        """
        Standardize a song object with consistent field names.

        Args:
            song: Raw song data from ytmusicapi
            include_stream_url: Whether to include stream URL

        Returns:
            Standardized song object
        """
        standardized = {}

        # Required fields
        standardized["videoId"] = song.get("videoId", "")
        standardized["title"] = song.get("title", "")

        # Artists
        artists = song.get("artists", [])
        standardized["artists"] = [
            {
                "name": artist.get("name", ""),
                "id": artist.get("id"),
                "browse_id": artist.get("browseId")
            }
            for artist in artists
            if artist.get("name") or artist.get("id")
        ]

        # Album
        album = song.get("album", {})
        if album:
            standardized["album"] = {
                "name": album.get("name", ""),
                "id": album.get("id"),
                "browse_id": album.get("browseId")
            }

        # Duration (standardize to seconds)
        duration_seconds = song.get("duration_seconds") or song.get("duration")
        if duration_seconds:
            standardized["duration"] = int(duration_seconds)
            # Convert to text format
            minutes = standardized["duration"] // 60
            seconds = standardized["duration"] % 60
            standardized["duration_text"] = f"{minutes}:{seconds:02d}"

        # Thumbnails - keep thumbnail (best) and thumbnails (all)
        thumbnails = song.get("thumbnails", [])
        if thumbnails:
            standardized["thumbnail"] = thumbnails[0].get("url", "")
            standardized["thumbnails"] = [
                {
                    "url": t.get("url", ""),
                    "width": t.get("width"),
                    "height": t.get("height")
                }
                for t in thumbnails
                if t.get("url")
            ]
        else:
            standardized["thumbnail"] = ""
            standardized["thumbnails"] = []

        # Stream URL (optional)
        if include_stream_url:
            standardized["stream_url"] = song.get("stream_url", "")

        # Explicit flag
        standardized["explicit"] = song.get("explicit", False)

        # Add any other fields that might be useful
        if "byArtist" in song:
            standardized["byArtist"] = song["byArtist"]
        if "officialVideo" in song:
            standardized["officialVideo"] = song["officialVideo"]

        return standardized

    @staticmethod
    def fix_response_field_names(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix inconsistent field names in a response dict.

        Args:
            data: Response dict with potentially inconsistent field names

        Returns:
            Fixed response dict
        """
        fixed = {}

        for key, value in data.items():
            # Fix duration fields
            if key == "duration_seconds" or key == "durationSec":
                new_key = "duration"
                if key in data:
                    fixed[new_key] = int(data[key])
                continue

            # Fix thumbnail/thumbnails
            if key == "thumbnail":
                fixed[key] = value
                if "thumbnails" not in fixed:
                    fixed["thumbnails"] = [value] if value else []
            elif key == "thumbnails" and isinstance(value, list) and value and isinstance(value[0], str):
                fixed[key] = value
                if "thumbnail" not in fixed:
                    fixed["thumbnail"] = value[0]
            else:
                fixed[key] = value

        return fixed
