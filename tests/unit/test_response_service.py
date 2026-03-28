"""Tests for ResponseService."""
import pytest
from app.services.response_service import ResponseService


class TestResponseService:
    """Test response standardization."""

    def test_standardize_song_object_basic(self):
        """Test basic song object standardization."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "artists": [{"name": "Test Artist", "id": "UC123"}],
            "album": {"name": "Test Album", "id": "PL123"},
            "duration": 180,
            "thumbnails": [{"url": "http://example.com/thumb", "width": 320, "height": 180}]
        }

        result = ResponseService.standardize_song_object(song, include_stream_url=True)

        assert result["videoId"] == "test123"
        assert result["title"] == "Test Song"
        assert len(result["artists"]) == 1
        assert result["artists"][0]["name"] == "Test Artist"
        assert result["album"]["name"] == "Test Album"
        assert result["duration"] == 180
        assert "duration_text" in result
        assert result["thumbnail"] == "http://example.com/thumb"
        assert result["stream_url"] == ""

    def test_standardize_with_duration_seconds(self):
        """Test that duration_seconds is converted to duration."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "duration_seconds": 180,
            "thumbnails": [{"url": "http://example.com/thumb"}]
        }

        result = ResponseService.standardize_song_object(song)

        assert result["duration"] == 180
        assert result["duration_text"] == "3:00"
        assert "duration_seconds" not in result

    def test_standardize_duration_text_format(self):
        """Test duration_text formatting."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "duration": 65,  # 1:05
            "thumbnails": [{"url": "http://example.com/thumb"}]
        }

        result = ResponseService.standardize_song_object(song)

        assert result["duration_text"] == "1:05"

    def test_standardize_no_artists(self):
        """Test song without artists."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "thumbnails": [{"url": "http://example.com/thumb"}]
        }

        result = ResponseService.standardize_song_object(song)

        assert result["artists"] == []

    def test_standardize_no_thumbnail(self):
        """Test song without thumbnail."""
        song = {
            "videoId": "test123",
            "title": "Test Song"
        }

        result = ResponseService.standardize_song_object(song)

        assert result["thumbnail"] == ""
        assert result["thumbnails"] == []

    def test_standardize_no_album(self):
        """Test song without album."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "artists": []
        }

        result = ResponseService.standardize_song_object(song)

        assert "album" not in result or result.get("album", {}) == {}

    def test_standardize_artist_fields(self):
        """Test artist field mapping."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "artists": [
                {"name": "Artist 1", "id": "UC123", "browseId": "UC123"},
                {"name": "Artist 2", "browseId": "UC456"}
            ]
        }

        result = ResponseService.standardize_song_object(song)

        assert len(result["artists"]) == 2
        assert result["artists"][0]["name"] == "Artist 1"
        assert result["artists"][0]["id"] == "UC123"
        assert result["artists"][0]["browse_id"] == "UC123"

    def test_standardize_explicit_flag(self):
        """Test explicit flag."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "explicit": True
        }

        result = ResponseService.standardize_song_object(song)

        assert result["explicit"] is True

    def test_standardize_stream_url_excluded_by_default(self):
        """Test that stream_url is excluded by default."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "stream_url": "http://stream.url"
        }

        result = ResponseService.standardize_song_object(song)

        assert "stream_url" not in result

    def test_standardize_stream_url_included_when_requested(self):
        """Test that stream_url is included when requested."""
        song = {
            "videoId": "test123",
            "title": "Test Song",
            "stream_url": "http://stream.url"
        }

        result = ResponseService.standardize_song_object(song, include_stream_url=True)

        assert result["stream_url"] == "http://stream.url"

    def test_fix_response_field_names_duration_seconds(self):
        """Test fixing duration_seconds field name."""
        data = {
            "videoId": "test123",
            "duration_seconds": 180
        }

        result = ResponseService.fix_response_field_names(data)

        assert "duration" in result
        assert result["duration"] == 180

    def test_fix_response_field_names_thumbnails(self):
        """Test fixing thumbnail/thumbnails field names."""
        data = {
            "videoId": "test123",
            "thumbnail": "http://example.com/thumb"
        }

        result = ResponseService.fix_response_field_names(data)

        assert result["thumbnail"] == "http://example.com/thumb"
        assert "thumbnails" in result
