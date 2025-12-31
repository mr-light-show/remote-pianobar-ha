"""Fixtures for Pianobar tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.pianobar.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Override async_setup_entry."""
    with patch(
        "custom_components.pianobar.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    mock_ws = MagicMock()
    mock_ws.closed = False
    mock_ws.send_str = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.__aiter__ = MagicMock(return_value=iter([]))
    return mock_ws


@pytest.fixture
def mock_coordinator(mock_websocket):
    """Mock PianobarCoordinator."""
    with patch(
        "custom_components.pianobar.coordinator.PianobarCoordinator"
    ) as mock_coord:
        coordinator = mock_coord.return_value
        coordinator.async_connect = AsyncMock()
        coordinator.async_disconnect = AsyncMock()
        coordinator.send_event = AsyncMock()
        coordinator.send_action = AsyncMock()
        coordinator.send_action_with_params = AsyncMock()
        coordinator._ws = mock_websocket
        coordinator.data = {
            "playing": False,
            "paused": False,
            "volume": 0,
            "maxGain": 10,
            "station": "",
            "stationId": "",
            "stations": [],
        }
        yield coordinator


@pytest.fixture
def mock_config_entry(hass: HomeAssistant):
    """Mock ConfigEntry."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Pianobar (127.0.0.1)",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 3000},
        entry_id="test_entry_id",
        unique_id="127.0.0.1:3000",
    )
    return entry


@pytest.fixture
def mock_station_data():
    """Mock station data."""
    return [
        {
            "id": "123456789",
            "name": "Test Station 1",
            "isQuickMix": False,
            "isQuickMixed": True,
        },
        {
            "id": "987654321",
            "name": "Test Station 2",
            "isQuickMix": False,
            "isQuickMixed": False,
        },
        {
            "id": "555555555",
            "name": "QuickMix",
            "isQuickMix": True,
            "isQuickMixed": False,
        },
    ]


@pytest.fixture
def mock_song_data():
    """Mock song data."""
    return {
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "coverArt": "https://example.com/art.jpg",
        "rating": 1,
        "duration": 240,
        "trackToken": "test_track_token",
        "songStationName": "Test Station",
    }


@pytest.fixture
def mock_process_event(mock_song_data):
    """Mock process event payload."""
    return {
        "playing": True,
        "paused": False,
        "volume": -5,
        "maxGain": 10,
        "station": "Test Station 1",
        "stationId": "123456789",
        "elapsed": 45,
        "song": mock_song_data,
    }

