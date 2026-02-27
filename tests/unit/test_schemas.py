"""Unit tests for Pydantic schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.search import SearchResult, SearchResponse, SearchSuggestionsResponse
from app.schemas.browse import (
    ArtistResponse,
    AlbumResponse,
    AlbumTrack,
    SongResponse,
    LyricsResponse,
)
from app.schemas.stream import StreamUrlResponse, StreamEnrichedItem, StreamBatchResponse
from app.schemas.playlist import PlaylistTrack, PlaylistResponse
from app.schemas.common import (
    Thumbnail,
    ArtistBasic,
    AlbumBasic,
    SongBasic,
    StreamingInfo,
    ErrorResponse,
    SuccessResponse,
)
from app.schemas.explore import (
    MoodCategory,
    MoodCategoriesResponse,
    ChartsTrack,
    ChartsResponse,
    MoodPlaylist,
    MoodPlaylistsResponse,
)
from app.schemas.podcast import (
    PodcastEpisode,
    PodcastChannelResponse,
    PodcastEpisodeResponse,
    PodcastResponse,
)


class TestSearchSchemas:
    """Test cases for search schemas."""

    def test_search_result_minimal(self):
        """Test SearchResult with minimal data."""
        result = SearchResult(title="Test Song")
        
        assert result.title == "Test Song"
        assert result.video_id is None
        assert result.result_type is None

    def test_search_result_full(self):
        """Test SearchResult with full data."""
        result = SearchResult(
            video_id="abc123",
            title="Test Song",
            result_type="song",
            artists=[{"name": "Artist"}],
            duration="3:45",
            thumbnails=[{"url": "https://example.com/thumb.jpg"}],
        )
        
        assert result.video_id == "abc123"
        assert result.title == "Test Song"
        assert result.result_type == "song"
        assert len(result.artists) == 1

    def test_search_result_extra_fields_allowed(self):
        """Test SearchResult allows extra fields."""
        result = SearchResult(
            title="Test",
            extra_field="extra_value",
        )
        
        assert result.title == "Test"

    def test_search_result_requires_title(self):
        """Test SearchResult requires title."""
        with pytest.raises(ValidationError):
            SearchResult()

    def test_search_response(self):
        """Test SearchResponse schema."""
        response = SearchResponse(
            results=[SearchResult(title="Song 1")],
            query="test",
        )
        
        assert response.query == "test"
        assert len(response.results) == 1

    def test_search_suggestions_response(self):
        """Test SearchSuggestionsResponse schema."""
        response = SearchSuggestionsResponse(
            suggestions=["suggestion 1", "suggestion 2"]
        )
        
        assert len(response.suggestions) == 2


class TestBrowseSchemas:
    """Test cases for browse schemas."""

    def test_artist_response(self):
        """Test ArtistResponse schema."""
        artist = ArtistResponse(
            name="Test Artist",
            description="An artist",
            subscribers="1M",
        )
        
        assert artist.name == "Test Artist"
        assert artist.subscribers == "1M"

    def test_album_track(self):
        """Test AlbumTrack schema."""
        track = AlbumTrack(
            video_id="track1",
            title="Track Title",
            duration="3:30",
        )
        
        assert track.video_id == "track1"
        assert track.title == "Track Title"

    def test_album_response(self):
        """Test AlbumResponse schema."""
        album = AlbumResponse(
            title="Album Title",
            year="2024",
            track_count=10,
            tracks=[AlbumTrack(title="Track 1")],
        )
        
        assert album.title == "Album Title"
        assert album.track_count == 10

    def test_song_response(self):
        """Test SongResponse schema."""
        song = SongResponse(
            video_id="song1",
            title="Song Title",
            duration="3:45",
        )
        
        assert song.video_id == "song1"

    def test_lyrics_response(self):
        """Test LyricsResponse schema."""
        lyrics = LyricsResponse(
            lyrics="Song lyrics here...",
            source="Musixmatch",
        )
        
        assert lyrics.lyrics == "Song lyrics here..."
        assert lyrics.source == "Musixmatch"


class TestStreamSchemas:
    """Test cases for stream schemas."""

    def test_stream_url_response(self):
        """Test StreamUrlResponse schema."""
        response = StreamUrlResponse(
            url="https://example.com/audio.m4a",
            title="Song Title",
            artist="Artist",
            duration=180,
        )
        
        assert response.url == "https://example.com/audio.m4a"
        assert response.duration == 180

    def test_stream_url_response_requires_url(self):
        """Test StreamUrlResponse requires url."""
        with pytest.raises(ValidationError):
            StreamUrlResponse(title="Song")

    def test_stream_enriched_item(self):
        """Test StreamEnrichedItem schema."""
        item = StreamEnrichedItem(
            video_id="video1",
            title="Song",
            stream_url="https://example.com/stream.m4a",
        )
        
        assert item.video_id == "video1"
        assert item.stream_url == "https://example.com/stream.m4a"

    def test_stream_batch_response(self):
        """Test StreamBatchResponse schema."""
        response = StreamBatchResponse(
            items=[StreamEnrichedItem(title="Song 1")],
            total=1,
        )
        
        assert response.total == 1
        assert len(response.items) == 1


class TestPlaylistSchemas:
    """Test cases for playlist schemas."""

    def test_playlist_track(self):
        """Test PlaylistTrack schema."""
        track = PlaylistTrack(
            video_id="track1",
            title="Track Title",
            duration="3:30",
            duration_seconds=210,
        )
        
        assert track.video_id == "track1"
        assert track.duration_seconds == 210

    def test_playlist_response(self):
        """Test PlaylistResponse schema."""
        playlist = PlaylistResponse(
            id="PL123",
            title="My Playlist",
            track_count=10,
            tracks=[PlaylistTrack(title="Track 1")],
        )
        
        assert playlist.id == "PL123"
        assert playlist.track_count == 10


class TestCommonSchemas:
    """Test cases for common schemas."""

    def test_thumbnail(self):
        """Test Thumbnail schema."""
        thumb = Thumbnail(
            url="https://example.com/thumb.jpg",
            width=480,
            height=360,
        )
        
        assert thumb.url == "https://example.com/thumb.jpg"
        assert thumb.width == 480

    def test_thumbnail_requires_url(self):
        """Test Thumbnail requires url."""
        with pytest.raises(ValidationError):
            Thumbnail(width=100)

    def test_artist_basic(self):
        """Test ArtistBasic schema."""
        artist = ArtistBasic(name="Artist Name", id="UC123")
        
        assert artist.name == "Artist Name"
        assert artist.id == "UC123"

    def test_artist_basic_requires_name(self):
        """Test ArtistBasic requires name."""
        with pytest.raises(ValidationError):
            ArtistBasic(id="UC123")

    def test_album_basic(self):
        """Test AlbumBasic schema."""
        album = AlbumBasic(name="Album Name")
        
        assert album.name == "Album Name"

    def test_song_basic(self):
        """Test SongBasic schema."""
        song = SongBasic(
            video_id="video1",
            title="Song Title",
            artists=[ArtistBasic(name="Artist")],
        )
        
        assert song.video_id == "video1"
        assert song.title == "Song Title"
        assert len(song.artists) == 1

    def test_song_basic_defaults(self):
        """Test SongBasic default values."""
        song = SongBasic(video_id="video1", title="Song")
        
        assert song.artists == []
        assert song.thumbnails == []

    def test_streaming_info(self):
        """Test StreamingInfo schema."""
        info = StreamingInfo(
            stream_url="https://example.com/stream.m4a",
            title="Song",
            duration=180,
        )
        
        assert info.stream_url == "https://example.com/stream.m4a"

    def test_error_response(self):
        """Test ErrorResponse schema."""
        error = ErrorResponse(
            error="NotFoundError",
            message="Resource not found",
        )
        
        assert error.error == "NotFoundError"
        assert error.message == "Resource not found"

    def test_success_response(self):
        """Test SuccessResponse schema."""
        success = SuccessResponse(success=True, message="Operation completed")
        
        assert success.success is True
        assert success.message == "Operation completed"

    def test_success_response_default(self):
        """Test SuccessResponse default values."""
        success = SuccessResponse()
        
        assert success.success is True


class TestExploreSchemas:
    """Test cases for explore schemas."""

    def test_mood_category(self):
        """Test MoodCategory schema."""
        category = MoodCategory(
            title="Cumbia",
            params="ggMPOg1uX3hRRFdlaEhHU09k",
        )
        
        assert category.title == "Cumbia"
        assert category.params == "ggMPOg1uX3hRRFdlaEhHU09k"

    def test_mood_categories_response(self):
        """Test MoodCategoriesResponse schema."""
        response = MoodCategoriesResponse(
            categories={"Genres": [MoodCategory(title="Rock")]}
        )
        
        assert "Genres" in response.categories

    def test_charts_track(self):
        """Test ChartsTrack schema."""
        track = ChartsTrack(
            video_id="chart1",
            title="Top Song",
            rank=1,
        )
        
        assert track.video_id == "chart1"
        assert track.rank == 1

    def test_charts_response(self):
        """Test ChartsResponse schema."""
        response = ChartsResponse(
            top_songs=[ChartsTrack(title="Song 1")],
            country="US",
        )
        
        assert response.country == "US"

    def test_mood_playlist(self):
        """Test MoodPlaylist schema."""
        playlist = MoodPlaylist(
            playlist_id="PL123",
            title="Chill Vibes",
            count=50,
        )
        
        assert playlist.playlist_id == "PL123"
        assert playlist.count == 50

    def test_mood_playlists_response(self):
        """Test MoodPlaylistsResponse schema."""
        response = MoodPlaylistsResponse(
            playlists=[MoodPlaylist(title="Playlist 1")],
            method="direct",
        )
        
        assert response.method == "direct"


class TestPodcastSchemas:
    """Test cases for podcast schemas."""

    def test_podcast_episode(self):
        """Test PodcastEpisode schema."""
        episode = PodcastEpisode(
            video_id="episode1",
            title="Episode Title",
            duration="45:00",
        )
        
        assert episode.video_id == "episode1"
        assert episode.duration == "45:00"

    def test_podcast_channel_response(self):
        """Test PodcastChannelResponse schema."""
        channel = PodcastChannelResponse(
            title="Podcast Channel",
            channel_id="UC123",
            episodes=[PodcastEpisode(title="Episode 1")],
        )
        
        assert channel.title == "Podcast Channel"
        assert len(channel.episodes) == 1

    def test_podcast_episode_response(self):
        """Test PodcastEpisodeResponse schema."""
        episode = PodcastEpisodeResponse(
            video_id="episode1",
            title="Episode Title",
            podcast={"title": "Parent Podcast"},
        )
        
        assert episode.podcast["title"] == "Parent Podcast"

    def test_podcast_response(self):
        """Test PodcastResponse schema."""
        podcast = PodcastResponse(
            id="podcast123",
            title="Tech Podcast",
            author="Tech Host",
            episodes=[PodcastEpisode(title="Episode 1")],
        )
        
        assert podcast.title == "Tech Podcast"
        assert podcast.author == "Tech Host"
