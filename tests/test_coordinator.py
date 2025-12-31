"""Test the Pianobar coordinator."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant

from custom_components.pianobar.coordinator import PianobarCoordinator


async def test_coordinator_connect_success(hass: HomeAssistant) -> None:
    """Test successful WebSocket connection."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send_str = AsyncMock()
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.ws_connect = AsyncMock(return_value=mock_ws)
        
        await coordinator.async_connect()
        
        assert coordinator._ws == mock_ws
        mock_ws.send_str.assert_called_once()  # query event


async def test_coordinator_connect_timeout(hass: HomeAssistant) -> None:
    """Test WebSocket connection timeout."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.ws_connect = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        
        with pytest.raises(ConnectionError):
            await coordinator.async_connect()


async def test_coordinator_disconnect(hass: HomeAssistant) -> None:
    """Test WebSocket disconnection."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.close = AsyncMock()
    coordinator._ws = mock_ws
    
    mock_session = AsyncMock()
    mock_session.closed = False
    mock_session.close = AsyncMock()
    coordinator._session = mock_session
    
    await coordinator.async_disconnect()
    
    mock_ws.close.assert_called_once()
    mock_session.close.assert_called_once()


async def test_handle_process_event(
    hass: HomeAssistant,
    mock_process_event,
    mock_song_data,
) -> None:
    """Test handling process event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    coordinator._handle_process_event(mock_process_event)
    
    assert coordinator.data["playing"] is True
    assert coordinator.data["paused"] is False
    assert coordinator.data["volume"] == -5
    assert coordinator.data["station"] == "Test Station 1"
    assert coordinator.data["song"] == mock_song_data


async def test_handle_start_event(hass: HomeAssistant, mock_song_data) -> None:
    """Test handling start event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    payload = {
        **mock_song_data,
        "station": "Test Station 1",
        "stationId": "123456789",
    }
    
    coordinator._handle_start_event(payload)
    
    assert coordinator.data["playing"] is True
    assert coordinator.data["paused"] is False
    assert coordinator.data["elapsed"] == 0
    assert coordinator.data["song"]["title"] == "Test Song"


async def test_handle_stop_event(hass: HomeAssistant) -> None:
    """Test handling stop event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Set up initial state
    coordinator.data["playing"] = True
    coordinator.data["song"] = {"title": "Test"}
    coordinator.data["elapsed"] = 30
    
    coordinator._handle_stop_event()
    
    assert coordinator.data["playing"] is False
    assert "song" not in coordinator.data
    assert "elapsed" not in coordinator.data


async def test_handle_progress_event(hass: HomeAssistant) -> None:
    """Test handling progress event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    coordinator.data["playing"] = True
    
    coordinator._handle_progress_event({"elapsed": 67, "duration": 240})
    
    assert coordinator.data["elapsed"] == 67


async def test_handle_volume_event(hass: HomeAssistant) -> None:
    """Test handling volume event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    coordinator._handle_volume_event(-10)
    
    assert coordinator.data["volume"] == -10


async def test_handle_play_state_event(hass: HomeAssistant) -> None:
    """Test handling playState event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    coordinator._handle_play_state_event({"paused": True})
    
    assert coordinator.data["paused"] is True


async def test_handle_stations_event(hass: HomeAssistant, mock_station_data) -> None:
    """Test handling stations event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    coordinator._handle_stations_event(mock_station_data)
    
    assert len(coordinator.data["stations"]) == 3
    assert coordinator.data["stations"][0]["name"] == "Test Station 1"


async def test_send_event(hass: HomeAssistant) -> None:
    """Test sending an event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send_str = AsyncMock()
    coordinator._ws = mock_ws
    
    await coordinator.send_event("test_event", {"key": "value"})
    
    mock_ws.send_str.assert_called_once()
    call_args = mock_ws.send_str.call_args[0][0]
    assert call_args.startswith('2["test_event"')
    assert '"key":"value"' in call_args or '"key": "value"' in call_args


async def test_send_action(hass: HomeAssistant) -> None:
    """Test sending an action."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send_str = AsyncMock()
    coordinator._ws = mock_ws
    
    await coordinator.send_action("playback.pause")
    
    mock_ws.send_str.assert_called_once()
    call_args = mock_ws.send_str.call_args[0][0]
    assert '"action"' in call_args
    assert '"playback.pause"' in call_args


async def test_handle_message_parse_event(hass: HomeAssistant) -> None:
    """Test parsing WebSocket message."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Mock process event message
    message = '2["volume",-10]'
    
    await coordinator._handle_message(message)
    
    assert coordinator.data["volume"] == -10


async def test_handle_message_invalid_format(hass: HomeAssistant) -> None:
    """Test handling invalid message format."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Invalid JSON
    message = '2["invalid'
    
    # Should not raise exception
    await coordinator._handle_message(message)


async def test_handle_message_non_event(hass: HomeAssistant) -> None:
    """Test handling non-event message."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Message type 0 (CONNECT) instead of 2 (EVENT)
    message = '0{"sid":"abc123"}'
    
    # Should be ignored
    await coordinator._handle_message(message)

