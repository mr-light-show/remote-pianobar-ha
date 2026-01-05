"""Test the Pianobar media player."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.pianobar.const import DOMAIN, MEDIA_TYPE_STATION
from custom_components.pianobar.media_player import PianobarMediaPlayer


async def test_media_player_state_idle(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test media player idle state."""
    mock_coordinator.data = {"playing": False, "paused": False, "station": "Test Station"}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.state == MediaPlayerState.IDLE


async def test_media_player_state_playing(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test media player playing state."""
    mock_coordinator.data = {"playing": True, "paused": False, "station": "Test Station"}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.state == MediaPlayerState.PLAYING


async def test_media_player_state_paused(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test media player paused state."""
    mock_coordinator.data = {"playing": True, "paused": True, "station": "Test Station"}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.state == MediaPlayerState.PAUSED


async def test_media_player_volume_level(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test media player volume level."""
    mock_coordinator.data = {"volume": 0.5, "maxGain": 10}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    # volume_level returns the raw value from coordinator data (already 0.0-1.0)
    assert player.volume_level == pytest.approx(0.5, rel=0.01)


async def test_media_player_source(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test media player source."""
    mock_coordinator.data = {"station": "Test Station"}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.source == "Test Station"


async def test_media_player_source_list(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
    mock_station_data,
) -> None:
    """Test media player source list."""
    mock_coordinator.data = {"stations": mock_station_data}
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.source_list == ["Test Station 1", "Test Station 2", "QuickMix"]


async def test_media_player_media_attributes(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
    mock_song_data,
) -> None:
    """Test media player media attributes."""
    mock_coordinator.data = {
        "song": mock_song_data,
        "elapsed": 45,
        "stationId": "123456789",
    }
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    assert player.media_title == "Test Song"
    assert player.media_artist == "Test Artist"
    assert player.media_album_name == "Test Album"
    assert player.media_image_url == "https://example.com/art.jpg"
    assert player.media_duration == 240
    assert player.media_position == 45
    assert player.media_content_id == "123456789"


async def test_media_player_select_source(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
    mock_station_data,
) -> None:
    """Test selecting a source."""
    mock_coordinator.data = {"stations": mock_station_data}
    mock_coordinator.send_event = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_select_source("Test Station 1")
    
    mock_coordinator.send_event.assert_called_once_with("station.change", "123456789")


async def test_media_player_play(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test play command."""
    mock_coordinator.send_action = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_media_play()
    
    mock_coordinator.send_action.assert_called_once_with("playback.play")


async def test_media_player_pause(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test pause command."""
    mock_coordinator.send_action = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_media_pause()
    
    mock_coordinator.send_action.assert_called_once_with("playback.pause")


async def test_media_player_next_track(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test next track command."""
    mock_coordinator.send_action = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_media_next_track()
    
    mock_coordinator.send_action.assert_called_once_with("playback.next")


async def test_media_player_set_volume(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test set volume command."""
    mock_coordinator.data = {"maxGain": 10}
    mock_coordinator.send_action_with_params = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_set_volume_level(0.75)
    
    mock_coordinator.send_action_with_params.assert_called_once()
    call_args = mock_coordinator.send_action_with_params.call_args
    assert call_args[0][0] == "volume.set"
    assert call_args[0][1]["volume"] == 75.0


async def test_media_player_volume_up(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test volume up command."""
    mock_coordinator.send_action = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_volume_up()
    
    mock_coordinator.send_action.assert_called_once_with("volume.up")


async def test_media_player_volume_down(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test volume down command."""
    mock_coordinator.send_action = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_volume_down()
    
    mock_coordinator.send_action.assert_called_once_with("volume.down")


async def test_media_player_play_media_by_id(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
    mock_station_data,
) -> None:
    """Test play media by station ID."""
    mock_coordinator.data = {"stations": mock_station_data}
    mock_coordinator.send_event = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_play_media(MEDIA_TYPE_STATION, "123456789")
    
    mock_coordinator.send_event.assert_called_once_with("station.change", "123456789")


async def test_media_player_play_media_by_name(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
    mock_station_data,
) -> None:
    """Test play media by station name."""
    mock_coordinator.data = {"stations": mock_station_data}
    mock_coordinator.send_event = AsyncMock()
    
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    await player.async_play_media(MediaType.MUSIC, "Test Station 2")
    
    mock_coordinator.send_event.assert_called_once_with("station.change", "987654321")


async def test_media_player_supported_features(
    hass: HomeAssistant,
    mock_config_entry,
    mock_coordinator,
) -> None:
    """Test supported features."""
    player = PianobarMediaPlayer(mock_coordinator, mock_config_entry)
    
    features = player.supported_features
    
    assert features & MediaPlayerEntityFeature.PAUSE
    assert features & MediaPlayerEntityFeature.PLAY
    assert features & MediaPlayerEntityFeature.VOLUME_SET
    assert features & MediaPlayerEntityFeature.VOLUME_STEP
    assert features & MediaPlayerEntityFeature.NEXT_TRACK
    assert features & MediaPlayerEntityFeature.SELECT_SOURCE
    assert features & MediaPlayerEntityFeature.BROWSE_MEDIA
    assert features & MediaPlayerEntityFeature.PLAY_MEDIA

