"""Tests for Pianobar select platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.pianobar.const import DOMAIN
from custom_components.pianobar.select import (
    PianobarAccountSelect,
    PianobarStationSelect,
    async_setup_entry,
)


def _attach_select_platform(entity: PianobarStationSelect | PianobarAccountSelect) -> None:
    """Provide platform_translations so translated entity names resolve in tests."""
    pl = MagicMock()
    pl.platform_name = "select"
    pl.domain = DOMAIN
    key = entity.translation_key or "station"
    label = "Station" if key == "station" else "Account"
    pl.platform_translations = {
        f"component.select.entity.{DOMAIN}.{key}.name": label,
    }
    entity.platform = pl


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
        _attach_select_platform(entity)

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
            "translation_key": "pianobar_device",
            "manufacturer": "Pandora",
            "model": "Pianobar",
        }


@pytest.fixture
def mock_coordinator_multi_account(mock_station_data):
    """Coordinator data with two accounts (multi-account UI)."""
    coordinator = MagicMock()
    coordinator.data = {
        "playing": True,
        "paused": False,
        "volume": 0,
        "station": "Test Station 1",
        "stationId": "123456789",
        "stations": mock_station_data,
        "accounts": [
            {"id": "work", "label": "Work"},
            {"id": "home", "label": "Home"},
        ],
        "current_account": {"id": "work", "label": "Work"},
    }
    coordinator.send_event = AsyncMock()
    coordinator.send_action_with_params = AsyncMock()
    coordinator.async_add_listener = MagicMock(return_value=lambda: None)
    return coordinator


class TestPianobarAccountSelect:
    """Tests for PianobarAccountSelect entity."""

    def test_account_entity_attributes(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """Account select uses correct name, icon, unique_id."""
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        _attach_select_platform(entity)
        assert entity.name == "Account"
        assert entity.icon == "mdi:account-switch"
        assert entity.unique_id == "test_entry_id_account_select"

    def test_account_options_and_current(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """Options list labels; current_option matches active account."""
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        assert entity.options == ["Work", "Home"]
        assert entity.current_option == "Work"

    def test_current_option_falls_back_to_id_when_no_label(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """current_account without label uses id if that id is in options."""
        mock_coordinator_multi_account.data["accounts"] = [
            {"id": "solo", "label": "solo"},
        ]
        mock_coordinator_multi_account.data["current_account"] = {"id": "solo"}
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        assert entity.current_option == "solo"

    def test_current_option_none_when_not_in_options(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """Unknown active account label yields None."""
        mock_coordinator_multi_account.data["current_account"] = {
            "id": "x",
            "label": "Ghost",
        }
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        assert entity.current_option is None

    @pytest.mark.asyncio
    async def test_account_async_select_option(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """Selecting an account sends app.pandora-reconnect with account_id."""
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        await entity.async_select_option("Home")
        mock_coordinator_multi_account.send_action_with_params.assert_called_once_with(
            "app.pandora-reconnect", {"account_id": "home"}
        )

    @pytest.mark.asyncio
    async def test_account_async_select_unknown_option(
        self, mock_coordinator_multi_account, mock_config_entry_for_select
    ):
        """Unknown account label does not call send_action_with_params."""
        entity = PianobarAccountSelect(
            mock_coordinator_multi_account, mock_config_entry_for_select
        )
        await entity.async_select_option("Nope")
        mock_coordinator_multi_account.send_action_with_params.assert_not_called()


@pytest.mark.asyncio
async def test_async_setup_entry_single_account_only_station_select(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    """One account configured: only station select entity."""
    coordinator = MagicMock()
    coordinator.data = {"stations": [], "accounts": [{"id": "a", "label": "Only"}]}
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator

    entities: list = []

    # AddEntitiesCallback is synchronous; platform calls it without await.
    def async_add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert len(entities) == 1
    assert isinstance(entities[0], PianobarStationSelect)


@pytest.mark.asyncio
async def test_async_setup_entry_multi_account_adds_account_select(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    """Two+ accounts: station select and account select."""
    coordinator = MagicMock()
    coordinator.data = {
        "stations": [],
        "accounts": [
            {"id": "a", "label": "A"},
            {"id": "b", "label": "B"},
        ],
    }
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = coordinator

    entities: list = []

    def async_add_entities(new_entities):
        entities.extend(new_entities)

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    assert len(entities) == 2
    assert isinstance(entities[0], PianobarStationSelect)
    assert isinstance(entities[1], PianobarAccountSelect)

