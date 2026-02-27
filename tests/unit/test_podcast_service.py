"""Unit tests for PodcastService."""
import pytest
from unittest.mock import MagicMock

from app.services.podcast_service import PodcastService
from app.core.exceptions import RateLimitError, AuthenticationError


@pytest.mark.asyncio
class TestPodcastService:
    """Test cases for PodcastService class."""


@pytest.mark.asyncio
class TestGetChannel:
    """Test cases for get_channel method."""

    async def test_get_channel_success(self, mock_ytmusic):
        """Test successful get_channel."""
        channel = {
            "title": "Test Channel",
            "channel_id": "UC123",
            "episodes": [],
        }
        mock_ytmusic.get_channel.return_value = channel
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_channel("UC123")
        
        assert result == channel
        mock_ytmusic.get_channel.assert_called_once()

    async def test_get_channel_with_limit(self, mock_ytmusic):
        """Test get_channel with limit parameter."""
        mock_ytmusic.get_channel.return_value = {}
        service = PodcastService(mock_ytmusic)
        
        await service.get_channel("UC123", limit=50)
        
        mock_ytmusic.get_channel.assert_called_once_with("UC123", 50)

    async def test_get_channel_empty(self, mock_ytmusic):
        """Test get_channel with empty result."""
        mock_ytmusic.get_channel.return_value = None
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_channel("UC123")
        
        assert result == {}

    async def test_get_channel_error(self, mock_ytmusic):
        """Test get_channel handles errors."""
        mock_ytmusic.get_channel.side_effect = Exception("API Error")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_channel("UC123")


@pytest.mark.asyncio
class TestGetChannelEpisodes:
    """Test cases for get_channel_episodes method."""

    async def test_get_channel_episodes_success(self, mock_ytmusic):
        """Test successful get_channel_episodes."""
        episodes = {
            "episodes": [
                {"videoId": "ep1", "title": "Episode 1"},
                {"videoId": "ep2", "title": "Episode 2"},
            ]
        }
        mock_ytmusic.get_channel_episodes.return_value = episodes
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_channel_episodes("UC123")
        
        assert result == episodes

    async def test_get_channel_episodes_with_params(self, mock_ytmusic):
        """Test get_channel_episodes with params parameter."""
        mock_ytmusic.get_channel_episodes.return_value = {}
        service = PodcastService(mock_ytmusic)
        
        await service.get_channel_episodes("UC123", limit=10, params="token123")
        
        mock_ytmusic.get_channel_episodes.assert_called_once_with(
            "UC123", 10, "token123"
        )

    async def test_get_channel_episodes_empty(self, mock_ytmusic):
        """Test get_channel_episodes with empty result."""
        mock_ytmusic.get_channel_episodes.return_value = None
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_channel_episodes("UC123")
        
        assert result == {}

    async def test_get_channel_episodes_error(self, mock_ytmusic):
        """Test get_channel_episodes handles errors."""
        mock_ytmusic.get_channel_episodes.side_effect = Exception("API Error")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_channel_episodes("UC123")


@pytest.mark.asyncio
class TestGetPodcast:
    """Test cases for get_podcast method."""

    async def test_get_podcast_success(self, mock_ytmusic, sample_podcast):
        """Test successful get_podcast."""
        mock_ytmusic.get_podcast.return_value = sample_podcast
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_podcast("podcast123")
        
        assert result == sample_podcast
        mock_ytmusic.get_podcast.assert_called_once()

    async def test_get_podcast_with_limit(self, mock_ytmusic):
        """Test get_podcast with limit parameter."""
        mock_ytmusic.get_podcast.return_value = {}
        service = PodcastService(mock_ytmusic)
        
        await service.get_podcast("podcast123", limit=50)
        
        mock_ytmusic.get_podcast.assert_called_once_with("podcast123", 50)

    async def test_get_podcast_empty(self, mock_ytmusic):
        """Test get_podcast with empty result."""
        mock_ytmusic.get_podcast.return_value = None
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_podcast("podcast123")
        
        assert result == {}

    async def test_get_podcast_error(self, mock_ytmusic):
        """Test get_podcast handles errors."""
        mock_ytmusic.get_podcast.side_effect = Exception("API Error")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_podcast("podcast123")


@pytest.mark.asyncio
class TestGetEpisode:
    """Test cases for get_episode method."""

    async def test_get_episode_success(self, mock_ytmusic, sample_episode):
        """Test successful get_episode."""
        mock_ytmusic.get_episode.return_value = sample_episode
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_episode("episode123")
        
        assert result == sample_episode
        mock_ytmusic.get_episode.assert_called_once_with("episode123")

    async def test_get_episode_empty(self, mock_ytmusic):
        """Test get_episode with empty result."""
        mock_ytmusic.get_episode.return_value = None
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_episode("episode123")
        
        assert result == {}

    async def test_get_episode_error(self, mock_ytmusic):
        """Test get_episode handles errors."""
        mock_ytmusic.get_episode.side_effect = Exception("API Error")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_episode("episode123")


@pytest.mark.asyncio
class TestGetEpisodesPlaylist:
    """Test cases for get_episodes_playlist method."""

    async def test_get_episodes_playlist_success(self, mock_ytmusic):
        """Test successful get_episodes_playlist."""
        playlist = {
            "playlistId": "PL123",
            "tracks": [
                {"videoId": "ep1", "title": "Episode 1"},
            ]
        }
        mock_ytmusic.get_episodes_playlist.return_value = playlist
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_episodes_playlist("podcast123")
        
        assert result == playlist

    async def test_get_episodes_playlist_with_limit(self, mock_ytmusic):
        """Test get_episodes_playlist with limit parameter."""
        mock_ytmusic.get_episodes_playlist.return_value = {}
        service = PodcastService(mock_ytmusic)
        
        await service.get_episodes_playlist("podcast123", limit=50)
        
        mock_ytmusic.get_episodes_playlist.assert_called_once_with("podcast123", 50)

    async def test_get_episodes_playlist_empty(self, mock_ytmusic):
        """Test get_episodes_playlist with empty result."""
        mock_ytmusic.get_episodes_playlist.return_value = None
        service = PodcastService(mock_ytmusic)
        
        result = await service.get_episodes_playlist("podcast123")
        
        assert result == {}

    async def test_get_episodes_playlist_error(self, mock_ytmusic):
        """Test get_episodes_playlist handles errors."""
        mock_ytmusic.get_episodes_playlist.side_effect = Exception("API Error")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(Exception):
            await service.get_episodes_playlist("podcast123")


@pytest.mark.asyncio
class TestPodcastServiceCaching:
    """Test caching behavior for PodcastService."""

    async def test_get_channel_has_cache_decorator(self, mock_ytmusic):
        """Test that get_channel has cache decorator."""
        service = PodcastService(mock_ytmusic)
        
        assert hasattr(service.get_channel, '__wrapped__')

    async def test_get_podcast_has_cache_decorator(self, mock_ytmusic):
        """Test that get_podcast has cache decorator."""
        service = PodcastService(mock_ytmusic)
        
        assert hasattr(service.get_podcast, '__wrapped__')

    async def test_get_episode_has_cache_decorator(self, mock_ytmusic):
        """Test that get_episode has cache decorator."""
        service = PodcastService(mock_ytmusic)
        
        assert hasattr(service.get_episode, '__wrapped__')


@pytest.mark.asyncio
class TestPodcastServiceErrorHandling:
    """Test error handling for PodcastService."""

    async def test_get_channel_auth_error(self, mock_ytmusic):
        """Test get_channel handles auth errors."""
        mock_ytmusic.get_channel.side_effect = Exception(
            "Expecting value: line 1 column 1"
        )
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(AuthenticationError):
            await service.get_channel("UC123")

    async def test_get_podcast_rate_limit_error(self, mock_ytmusic):
        """Test get_podcast handles rate limit errors."""
        mock_ytmusic.get_podcast.side_effect = Exception("429 Rate limit")
        service = PodcastService(mock_ytmusic)
        
        with pytest.raises(RateLimitError):
            await service.get_podcast("podcast123")
