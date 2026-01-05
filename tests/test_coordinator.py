"""Test the Pianobar coordinator."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant

from custom_components.pianobar.coordinator import PianobarCoordinator


async def test_coordinator_connect_success(hass: HomeAssistant) -> None:
    """Test successful WebSocket connection."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Create a mock WebSocket that blocks on iteration to prevent immediate listener exit
    async def infinite_iter():
        # Keep the listener task blocked
        await asyncio.sleep(100)  # This will be cancelled by disconnect
        
    mock_ws = AsyncMock()
    mock_ws.closed = False
    mock_ws.send_str = AsyncMock()
    mock_ws.close = AsyncMock()
    # Use a mock that just blocks instead of immediately ending
    mock_ws.__aiter__ = MagicMock(return_value=AsyncIteratorMock())
    
    mock_session = AsyncMock()
    mock_session.ws_connect = AsyncMock(return_value=mock_ws)
    mock_session.closed = False
    mock_session.close = AsyncMock()
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        await coordinator.async_connect()
        
        assert coordinator._ws == mock_ws
        mock_ws.send_str.assert_called_once()  # query event
        
        # Clean up - set closing flag first, then disconnect
        await coordinator.async_disconnect()


class AsyncIteratorMock:
    """Mock async iterator that blocks until cancelled."""
    
    async def __anext__(self):
        # Block forever (will be cancelled on disconnect)
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            raise StopAsyncIteration
        raise StopAsyncIteration


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
    assert coordinator.data["volume"] == -0.05  # Wire protocol sends -5, converted to -5/100
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
    
    assert coordinator.data["volume"] == -0.1  # Wire protocol sends -10, converted to -10/100


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
    
    assert coordinator.data["volume"] == -0.1  # Wire protocol sends -10, converted to -10/100


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


async def test_handle_song_explanation_event(hass: HomeAssistant) -> None:
    """Test handling song.explanation event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    message = '2["song.explanation",{"explanation":"Test explanation text"}]'
    
    await coordinator._handle_message(message)
    
    assert coordinator._response_data["song_explanation"] == "Test explanation text"


async def test_handle_upcoming_result_event(hass: HomeAssistant) -> None:
    """Test handling query.upcoming.result event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    upcoming_songs = [
        {"title": "Song 1", "artist": "Artist 1"},
        {"title": "Song 2", "artist": "Artist 2"},
    ]
    message = f'2["query.upcoming.result",{json.dumps(upcoming_songs)}]'
    
    await coordinator._handle_message(message)
    
    assert len(coordinator._response_data["upcoming"]) == 2
    assert coordinator._response_data["upcoming"][0]["title"] == "Song 1"


async def test_handle_station_info_event(hass: HomeAssistant) -> None:
    """Test handling stationInfo event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    station_info = {
        "artistSeeds": [{"seedId": "AS123", "name": "Test Artist"}],
        "songSeeds": [],
        "stationSeeds": [],
        "feedback": [],
    }
    message = f'2["stationInfo",{json.dumps(station_info)}]'
    
    await coordinator._handle_message(message)
    
    assert len(coordinator._response_data["station_info"]["artistSeeds"]) == 1
    assert coordinator._response_data["station_info"]["artistSeeds"][0]["name"] == "Test Artist"


async def test_handle_station_modes_event(hass: HomeAssistant) -> None:
    """Test handling stationModes event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    modes_data = {
        "modes": [
            {"id": 0, "name": "My Station", "active": True},
            {"id": 1, "name": "Crowd Faves", "active": False},
        ]
    }
    message = f'2["stationModes",{json.dumps(modes_data)}]'
    
    await coordinator._handle_message(message)
    
    assert len(coordinator._response_data["station_modes"]) == 2
    assert coordinator._response_data["station_modes"][0]["name"] == "My Station"


async def test_get_response_data(hass: HomeAssistant) -> None:
    """Test getting and clearing response data."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Set some response data
    coordinator._response_data["test_key"] = "test_value"
    
    # Get data (should clear it)
    result = coordinator.get_response_data("test_key")
    assert result == "test_value"
    
    # Should be cleared now
    result2 = coordinator.get_response_data("test_key")
    assert result2 is None


async def test_wait_for_response_timeout(hass: HomeAssistant) -> None:
    """Test waiting for response with timeout."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Wait for data that never arrives (short timeout)
    result = await coordinator.wait_for_response("missing_key", timeout=0.1)
    
    assert result is None


async def test_wait_for_response_success(hass: HomeAssistant) -> None:
    """Test waiting for response successfully."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    # Simulate async data arrival
    async def set_data():
        await asyncio.sleep(0.05)
        coordinator._response_data["test_key"] = "test_value"
    
    # Start both tasks
    import asyncio
    data_task = asyncio.create_task(set_data())
    result = await coordinator.wait_for_response("test_key", timeout=1.0)
    await data_task
    
    assert result == "test_value"


async def test_handle_search_results_event(hass: HomeAssistant) -> None:
    """Test handling searchResults event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    search_results = {
        "categories": [
            {
                "name": "Artists",
                "results": [
                    {"name": "Test Artist", "musicId": "R123"}
                ]
            },
            {
                "name": "Songs",
                "results": [
                    {"title": "Test Song", "artist": "Test Artist", "musicId": "S456"}
                ]
            }
        ]
    }
    message = f'2["searchResults",{json.dumps(search_results)}]'
    
    await coordinator._handle_message(message)
    
    assert "search_results" in coordinator._response_data
    assert len(coordinator._response_data["search_results"]["categories"]) == 2
    assert coordinator._response_data["search_results"]["categories"][0]["name"] == "Artists"


async def test_handle_genres_event(hass: HomeAssistant) -> None:
    """Test handling genres event."""
    coordinator = PianobarCoordinator(hass, "127.0.0.1", 3000)
    
    genres_data = {
        "categories": [
            {
                "name": "Rock",
                "genres": [
                    {"name": "Classic Rock", "musicId": "G100"},
                    {"name": "Alternative Rock", "musicId": "G101"}
                ]
            },
            {
                "name": "Pop",
                "genres": [
                    {"name": "Today's Hits", "musicId": "G200"}
                ]
            }
        ]
    }
    message = f'2["genres",{json.dumps(genres_data)}]'
    
    await coordinator._handle_message(message)
    
    assert "genres" in coordinator._response_data
    assert len(coordinator._response_data["genres"]["categories"]) == 2
    assert coordinator._response_data["genres"]["categories"][0]["name"] == "Rock"
    assert len(coordinator._response_data["genres"]["categories"][0]["genres"]) == 2

