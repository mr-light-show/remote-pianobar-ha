"""Tests for Pianobar select platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.pianobar.const import DOMAIN
from custom_components.pianobar.select import PianobarStationSelect


@pytest.fixture
def mock_coordinator_for_select(mock_station_data):
    """Create a mock coordinator for select tests."""
    coordinator = MagicMock()
    coordinator.data = {
        "playing": True,
        "paused": False,
        "volume": 0,
        "station": "Test Station 1",
        "stationId": "123456789",
        "stations": mock_station_data,
    }
    coordinator.send_event = AsyncMock()
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


@pytest.fixture
def mock_config_entry_for_select():
    """Create a mock config entry for select tests."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {CONF_HOST: "127.0.0.1", CONF_PORT: 3000}
    return entry


class TestPianobarStationSelect:
    """Tests for PianobarStationSelect entity."""

    def test_entity_creation(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test entity is created with correct attributes."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.name == "Station"
        assert entity.icon == "mdi:radio"
        assert entity.unique_id == "test_entry_id_station_select"

    def test_options_populated_from_stations(
        self, mock_coordinator_for_select, mock_config_entry_for_select, mock_station_data
    ):
        """Test options are populated from station list."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        options = entity.options
        assert len(options) == 3
        assert "Test Station 1" in options
        assert "Test Station 2" in options
        assert "QuickMix" in options

    def test_options_empty_when_no_stations(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test options are empty when no stations available."""
        mock_coordinator_for_select.data["stations"] = []
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.options == []

    def test_current_option_reflects_current_station(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test current_option returns the current station."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.current_option == "Test Station 1"

    def test_current_option_none_when_no_station(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test current_option is None when no station selected."""
        mock_coordinator_for_select.data["station"] = ""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.current_option is None

    def test_current_option_none_when_station_not_in_options(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test current_option is None when station is not in options."""
        mock_coordinator_for_select.data["station"] = "Unknown Station"
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.current_option is None

    @pytest.mark.asyncio
    async def test_select_option_sends_station_change(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test selecting an option sends station.change event."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        await entity.async_select_option("Test Station 2")

        mock_coordinator_for_select.send_event.assert_called_once_with(
            "station.change", "987654321"
        )

    @pytest.mark.asyncio
    async def test_select_option_with_quickmix(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test selecting QuickMix sends correct station ID."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        await entity.async_select_option("QuickMix")

        mock_coordinator_for_select.send_event.assert_called_once_with(
            "station.change", "555555555"
        )

    @pytest.mark.asyncio
    async def test_select_unknown_option_does_nothing(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test selecting unknown option does not send event."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        await entity.async_select_option("Non-existent Station")

        mock_coordinator_for_select.send_event.assert_not_called()

    def test_device_info(
        self, mock_coordinator_for_select, mock_config_entry_for_select
    ):
        """Test device info is set correctly."""
        entity = PianobarStationSelect(
            mock_coordinator_for_select, mock_config_entry_for_select
        )

        assert entity.device_info == {
            "identifiers": {(DOMAIN, "test_entry_id")},
            "name": "Pianobar",
            "manufacturer": "Pandora",
            "model": "Pianobar",
        }

