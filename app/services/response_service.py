"""Service for standardizing API responses."""
from typing import Any, Dict, Optional, List, Union
import datetime


class ResponseService:
    """Service for creating standardized API responses."""

    @staticmethod
    def parse_duration(value: Any) -> tuple[Optional[int], Optional[str]]:
        """
        Parse duration from any ytmusicapi format to (seconds, text).
        
        Handles:
        - int: seconds directly (e.g., 180)
        - str "3:45": MM:SS format
        - str "1:17:00": HH:MM:SS format
        - str "length" from watch playlist
        
        Returns:
            Tuple of (duration_seconds, duration_text)
        """
        if value is None:
            return (None, None)
        
        # Already int
        if isinstance(value, int):
            return (value, f"{value//60}:{value%60:02d}")
        
        # String formats
        if isinstance(value, str) and ":" in value:
            parts = value.split(":")
            try:
                if len(parts) == 2:
                    # "3:45" -> MM:SS
                    seconds = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    # "1:17:00" -> HH:MM:SS
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    return (None, None)
                return (seconds, value)
            except (ValueError, IndexError):
                return (None, None)
        
        return (None, None)

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
        include_stream_url: bool = False,
        include_feedback_tokens: bool = False,
        include_library_status: bool = False
    ) -> Dict[str, Any]:
        """
        Standardize a song object with consistent field names.
        
        STRICT MODE: Converts all ytmusicapi variations to standard format.

        Args:
            song: Raw song data from ytmusicapi
            include_stream_url: Whether to include stream URL
            include_feedback_tokens: Whether to include like/dislike tokens
            include_library_status: Whether to include inLibrary, likeStatus

        Returns:
            Standardized song object
        """
        standardized = {}

        # videoId - REQUIRED (strict mode: error if missing)
        video_id = song.get("videoId") or song.get("video_id")
        if not video_id:
            raise ValueError("videoId is required for song normalization")
        standardized["videoId"] = video_id

        # title
        standardized["title"] = song.get("title", "")

        # Artists - normalize id/browseId
        artists = song.get("artists", [])
        standardized["artists"] = [
            {
                "name": artist.get("name", ""),
                "id": artist.get("id") or artist.get("browseId") or artist.get("browse_id"),
                "browse_id": artist.get("browseId") or artist.get("browse_id")
            }
            for artist in artists
            if artist.get("name") or artist.get("id") or artist.get("browseId")
        ]

        # Album - normalize id/browseId
        album = song.get("album", {})
        if album:
            standardized["album"] = {
                "name": album.get("name", ""),
                "id": album.get("id") or album.get("browseId") or album.get("browse_id"),
                "browse_id": album.get("browseId") or album.get("browse_id")
            }

        # Duration - handle ALL formats: duration_seconds, duration, length
        # Priority: duration_seconds (int) > duration (int/str) > length (str)
        duration_val = (
            song.get("duration_seconds") or 
            song.get("duration") or 
            song.get("length")
        )
        
        if duration_val:
            seconds, text = ResponseService.parse_duration(duration_val)
            if seconds is not None:
                standardized["duration"] = seconds
                standardized["duration_text"] = text or f"{seconds//60}:{seconds%60:02d}"
        else:
            standardized["duration"] = None
            standardized["duration_text"] = None

        # Thumbnails - always pick the highest resolution one
        thumbnails = song.get("thumbnails", [])
        if thumbnails:
            # Sort by width*height to find the best quality one
            sorted_thumbnails = sorted(
                thumbnails, 
                key=lambda x: (x.get("width", 0) or 0) * (x.get("height", 0) or 0), 
                reverse=True
            )
            best_thumb = sorted_thumbnails[0].get("url", "")
            
            # If it's a YouTube image, we can try to force maxresdefault
            if "i.ytimg.com" in best_thumb and video_id:
                best_thumb = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            elif "googleusercontent.com" in best_thumb:
                # Force high resolution for googleusercontent images
                import re
                best_thumb = re.sub(r'=w\d+-h\d+', '=w800-h800', best_thumb)
                
            standardized["thumbnail"] = best_thumb
            standardized["thumbnails"] = sorted_thumbnails
        elif video_id:
            # Fallback to YouTube maxres if no thumbnails provided but we have videoId
            standardized["thumbnail"] = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            standardized["thumbnails"] = [{"url": standardized["thumbnail"], "width": 1280, "height": 720}]
        else:
            standardized["thumbnail"] = ""
            standardized["thumbnails"] = []

        # Stream URL (optional)
        if include_stream_url:
            standardized["stream_url"] = song.get("stream_url") or song.get("url") or ""

        # Explicit flag
        standardized["explicit"] = song.get("isExplicit") or song.get("explicit", False)

        # Feedback tokens (optional)
        if include_feedback_tokens:
            ft = song.get("feedbackTokens", {})
            standardized["feedback_tokens"] = {
                "add": ft.get("add", ""),
                "remove": ft.get("remove", "")
            }

        # Library status (optional)
        if include_library_status:
            standardized["in_library"] = song.get("inLibrary", False)
            standardized["like_status"] = song.get("likeStatus", "INDIFFERENT")

        # Preserve additional useful fields
        if "byArtist" in song:
            standardized["byArtist"] = song["byArtist"]
        if "officialVideo" in song:
            standardized["officialVideo"] = song["officialVideo"]
        if "videoType" in song:
            standardized["videoType"] = song["videoType"]
        if "setVideoId" in song:
            standardized["setVideoId"] = song["setVideoId"]

        return standardized

    @staticmethod
    def normalize_song_player_response(raw: dict) -> dict:
        """
        Normalize response from yt.get_song() - the raw YouTube player response.
        
        This is the CRITICAL normalization for /browse/song/{id} endpoint.
        Extracts only necessary fields from the >100KB raw response.

        Args:
            raw: Raw response from ytmusicapi.get_song()

        Returns:
            Normalized song metadata dict
        """
        # 0. Validate raw is a dict - if not, raise descriptive error
        if not isinstance(raw, dict):
            raise ValueError(f"Expected dict response, got {type(raw).__name__}: {raw}")

        # 1. Verify playability
        playability = raw.get("playabilityStatus", {})
        if not isinstance(playability, dict):
            raise ValueError(f"playabilityStatus is not a dict: {type(playability).__name__}")
        
        playability_status = playability.get("status", "ERROR")
        
        if playability_status != "OK":
            raise ValueError(
                f"Video not playable: {playability.get('reason', 'Unknown')}"
            )

        # 2. Extract video details - validate it's a dict
        video_details = raw.get("videoDetails", {})
        if not isinstance(video_details, dict):
            raise ValueError(f"videoDetails is not a dict: {type(video_details).__name__}")
        
        # 3. Find best audio stream
        streaming = raw.get("streamingData", {})
        audio_url = None
        
        # Check formats first - validate each format is a dict
        for f in streaming.get("formats", []):
            if not isinstance(f, dict):
                continue
            mime_type = f.get("mimeType", "")
            if mime_type.startswith("audio/"):
                url = f.get("url")
                if url:
                    audio_url = url
                    break
        
        # Then check adaptiveFormats - validate each format is a dict
        if not audio_url:
            for f in streaming.get("adaptiveFormats", []):
                if not isinstance(f, dict):
                    continue
                mime_type = f.get("mimeType", "")
                if mime_type.startswith("audio/"):
                    # Try direct URL first
                    url = f.get("url")
                    if not url:
                        # Handle signatureCipher (rare case)
                        sig_cipher = f.get("signatureCipher", {})
                        if isinstance(sig_cipher, dict):
                            url = sig_cipher.get("url")
                    if url:
                        audio_url = url
                        break

        # 4. Parse duration (lengthSeconds is STRING!)
        length_seconds = video_details.get("lengthSeconds", "0")
        try:
            duration_seconds = int(length_seconds)
        except (ValueError, TypeError):
            duration_seconds = 0

        # 5. Extract thumbnails
        # IMPORTANT: videoDetails.thumbnail can be either a list or an object with "thumbnails" key
        thumbnail_raw = video_details.get("thumbnail")
        thumbnails = []
        if thumbnail_raw:
            if isinstance(thumbnail_raw, list):
                thumbnails = thumbnail_raw
            elif isinstance(thumbnail_raw, dict):
                thumbnails = thumbnail_raw.get("thumbnails", [])

        # 6. Extract artists
        # IMPORTANT: videoDetails.author is a STRING (author name), not a dict!
        # Schema: videoDetails.author: str (not object with .get())
        author_raw = video_details.get("author", "")
        channel_id = video_details.get("channelId", "")
        
        artists = []
        if author_raw and isinstance(author_raw, str):
            artists = [{
                "name": author_raw,
                "id": channel_id,
                "browse_id": channel_id
            }]
        elif author_raw and isinstance(author_raw, dict):
            # Fallback para casos extremos donde sea dict
            artist_name = author_raw.get("name", "")
            if artist_name:
                artists = [{
                    "name": artist_name,
                    "id": channel_id,
                    "browse_id": channel_id
                }]

        # 7. Build normalized response
        # Safe thumbnail extraction
        thumbnail_url = None
        if thumbnails and isinstance(thumbnails[0], dict):
            thumbnail_url = thumbnails[0].get("url")

        return {
            "video_id": video_details.get("videoId"),
            "title": video_details.get("title"),
            "artists": artists,
            "album": None,  # get_song doesn't return album info
            "duration": duration_seconds,
            "duration_text": f"{duration_seconds//60}:{duration_seconds%60:02d}",
            "thumbnails": thumbnails,
            "thumbnail": thumbnail_url,
            "stream_url": audio_url,
            "is_explicit": video_details.get("isExplicit", False),
            "playability_status": playability_status,
            "video_type": video_details.get("videoType", "MUSIC_VIDEO_TYPE_ATV"),
            "keywords": video_details.get("keywords", []),
            "short_description": video_details.get("shortDescription", ""),
            "view_count": video_details.get("viewCount", "0"),
        }

    @staticmethod
    def standardize_artist_object(artist: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize artist object from any ytmusicapi source.
        
        Args:
            artist: Raw artist data

        Returns:
            Standardized artist dict
        """
        return {
            "id": artist.get("id") or artist.get("channelId") or artist.get("browseId"),
            "name": artist.get("name") or artist.get("artist", ""),
            "browse_id": artist.get("browseId") or artist.get("channelId"),
            "subscribers": artist.get("subscribers", ""),
            "thumbnails": artist.get("thumbnails", []),
            "thumbnail": (
                artist.get("thumbnails", [{}])[0].get("url") 
                if artist.get("thumbnails") else None
            )
        }

    @staticmethod
    def standardize_album_object(album: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize album object from any ytmusicapi source.
        
        Args:
            album: Raw album data

        Returns:
            Standardized album dict
        """
        return {
            "id": album.get("id") or album.get("browseId"),
            "name": album.get("name", ""),
            "browse_id": album.get("browseId"),
            "year": album.get("year"),
            "thumbnails": album.get("thumbnails", []),
            "thumbnail": (
                album.get("thumbnails", [{}])[0].get("url") 
                if album.get("thumbnails") else None
            )
        }

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