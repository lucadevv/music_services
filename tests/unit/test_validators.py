"""Unit tests for input validators."""
import pytest
from app.core.validators import (
    validate_video_id,
    validate_channel_id,
    validate_playlist_id,
    validate_browse_id,
    validate_search_query,
    validate_limit,
    validate_search_filter,
    sanitize_string,
)
from app.core.exceptions import ValidationError


class TestValidateVideoId:
    """Tests for validate_video_id function."""

    def test_valid_video_id(self):
        """Test with valid 11-character video ID."""
        result = validate_video_id("rMbATaj7Il8")
        assert result == "rMbATaj7Il8"

    def test_valid_video_id_with_underscore(self):
        """Test with valid video ID containing underscore."""
        result = validate_video_id("abc_DEF1234")
        assert result == "abc_DEF1234"

    def test_valid_video_id_with_hyphen(self):
        """Test with valid video ID containing hyphen."""
        result = validate_video_id("abc-DEF1234")
        assert result == "abc-DEF1234"

    def test_empty_video_id(self):
        """Test with empty video ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_video_id("")
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert "requerido" in exc_info.value.message.lower()

    def test_none_video_id(self):
        """Test with None video ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_video_id(None)
        
        assert exc_info.value.status_code == 400

    def test_too_short_video_id(self):
        """Test with too short video ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_video_id("short")
        
        assert exc_info.value.details["expected_length"] == 11
        assert exc_info.value.details["actual_length"] == 5

    def test_too_long_video_id(self):
        """Test with too long video ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_video_id("rMbATaj7Il8extra")
        
        assert exc_info.value.details["expected_length"] == 11

    def test_invalid_characters_video_id(self):
        """Test with invalid characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_video_id("rMbATaj7Il!")
        
        assert "caracteres inválidos" in exc_info.value.message


class TestValidateChannelId:
    """Tests for validate_channel_id function."""

    def test_valid_channel_id(self):
        """Test with valid channel ID starting with UC."""
        result = validate_channel_id("UCyPbsv_g9MHXLns1GrT2HQw")
        assert result == "UCyPbsv_g9MHXLns1GrT2HQw"

    def test_empty_channel_id(self):
        """Test with empty channel ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_channel_id("")
        
        assert "requerido" in exc_info.value.message.lower()

    def test_invalid_prefix_channel_id(self):
        """Test with invalid prefix raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_channel_id("ABCD123456789012345678")
        
        assert "UC" in exc_info.value.message

    def test_wrong_length_channel_id(self):
        """Test with wrong length raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_channel_id("UCshort")
        
        assert exc_info.value.details["expected_length"] == 24


class TestValidatePlaylistId:
    """Tests for validate_playlist_id function."""

    def test_valid_playlist_id(self):
        """Test with valid playlist ID."""
        result = validate_playlist_id("PLrAXtmRdnEQy4TyP9kDHq")
        assert result == "PLrAXtmRdnEQy4TyP9kDHq"

    def test_valid_short_playlist_id(self):
        """Test with valid short playlist ID."""
        result = validate_playlist_id("PL")
        assert result == "PL"

    def test_empty_playlist_id(self):
        """Test with empty playlist ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_playlist_id("")
        
        assert "requerido" in exc_info.value.message.lower()

    def test_too_short_playlist_id(self):
        """Test with too short playlist ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_playlist_id("P")
        
        assert "corto" in exc_info.value.message.lower()

    def test_invalid_characters_playlist_id(self):
        """Test with invalid characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_playlist_id("PL_invalid!@#")
        
        assert "caracteres inválidos" in exc_info.value.message


class TestValidateBrowseId:
    """Tests for validate_browse_id function."""

    def test_valid_browse_id(self):
        """Test with valid browse ID."""
        result = validate_browse_id("MPmZMjJhYjM5MzY")
        assert result == "MPmZMjJhYjM5MzY"

    def test_empty_browse_id(self):
        """Test with empty browse ID raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_browse_id("")
        
        assert "requerido" in exc_info.value.message.lower()


class TestValidateSearchQuery:
    """Tests for validate_search_query function."""

    def test_valid_query(self):
        """Test with valid search query."""
        result = validate_search_query("cumbia peruana")
        assert result == "cumbia peruana"

    def test_query_with_leading_trailing_spaces(self):
        """Test that query is stripped of whitespace."""
        result = validate_search_query("  cumbia  ")
        assert result == "cumbia"

    def test_empty_query(self):
        """Test with empty query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query("")
        
        assert "requerido" in exc_info.value.message.lower()

    def test_whitespace_only_query(self):
        """Test with whitespace-only query raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query("   ")
        
        assert "vacío" in exc_info.value.message.lower()

    def test_too_long_query(self):
        """Test with too long query raises ValidationError."""
        long_query = "a" * 250
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query(long_query)
        
        assert exc_info.value.details["max_length"] == 200


class TestValidateLimit:
    """Tests for validate_limit function."""

    def test_valid_limit(self):
        """Test with valid limit."""
        result = validate_limit(50)
        assert result == 50

    def test_minimum_limit(self):
        """Test with minimum limit."""
        result = validate_limit(1)
        assert result == 1

    def test_maximum_limit(self):
        """Test with maximum limit."""
        result = validate_limit(100)
        assert result == 100

    def test_below_minimum(self):
        """Test with limit below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_limit(0)
        
        assert exc_info.value.details["min_value"] == 1

    def test_above_maximum(self):
        """Test with limit above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_limit(150)
        
        assert exc_info.value.details["max_value"] == 100

    def test_custom_range(self):
        """Test with custom min/max values."""
        result = validate_limit(5, min_val=1, max_val=10)
        assert result == 5


class TestValidateSearchFilter:
    """Tests for validate_search_filter function."""

    def test_valid_filter_songs(self):
        """Test with valid 'songs' filter."""
        result = validate_search_filter("songs")
        assert result == "songs"

    def test_valid_filter_videos(self):
        """Test with valid 'videos' filter."""
        result = validate_search_filter("videos")
        assert result == "videos"

    def test_valid_filter_albums(self):
        """Test with valid 'albums' filter."""
        result = validate_search_filter("albums")
        assert result == "albums"

    def test_none_filter(self):
        """Test with None filter returns None."""
        result = validate_search_filter(None)
        assert result is None

    def test_invalid_filter(self):
        """Test with invalid filter raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_filter("invalid_filter")
        
        assert "inválido" in exc_info.value.message.lower()
        assert "valid_values" in exc_info.value.details


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_normal_string(self):
        """Test with normal string."""
        result = sanitize_string("Hello World")
        assert result == "Hello World"

    def test_string_with_control_chars(self):
        """Test that control characters are removed."""
        result = sanitize_string("Hello\x00World")
        assert result == "HelloWorld"

    def test_string_with_newlines_preserved(self):
        """Test that newlines are preserved."""
        result = sanitize_string("Hello\nWorld")
        assert result == "Hello\nWorld"

    def test_long_string_truncated(self):
        """Test that long strings are truncated."""
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_empty_string(self):
        """Test with empty string."""
        result = sanitize_string("")
        assert result == ""
