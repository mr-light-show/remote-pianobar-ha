"""Test the Pianobar integration init."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.pianobar.const import (
    DOMAIN,
    SERVICE_BAN_SONG,
    SERVICE_CREATE_STATION,
    SERVICE_DELETE_STATION,
    SERVICE_LOVE_SONG,
    SERVICE_RENAME_STATION,
    SERVICE_TIRED_OF_SONG,
)


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test setting up the integration."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        
        # Check services are registered
        assert hass.services.has_service(DOMAIN, SERVICE_LOVE_SONG)
        assert hass.services.has_service(DOMAIN, SERVICE_BAN_SONG)
        assert hass.services.has_service(DOMAIN, SERVICE_TIRED_OF_SONG)
        assert hass.services.has_service(DOMAIN, SERVICE_CREATE_STATION)
        assert hass.services.has_service(DOMAIN, SERVICE_RENAME_STATION)
        assert hass.services.has_service(DOMAIN, SERVICE_DELETE_STATION)


async def test_async_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test setup with connection error."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock(side_effect=Exception("Connection failed"))
        
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)


async def test_async_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test unloading the integration."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.async_disconnect = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        mock_coordinator.async_disconnect.assert_called_once()
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_service_love_song(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test love_song service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_action = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_LOVE_SONG,
            {},
            blocking=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("song.love")


async def test_service_ban_song(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test ban_song service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_action = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_BAN_SONG,
            {},
            blocking=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("song.ban")


async def test_service_create_station(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test create_station service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.data = {
            "playing": True,
            "song": {"trackToken": "test_token"},
        }
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CREATE_STATION,
            {"type": "artist"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.createFrom"
        assert call_args[1]["trackToken"] == "test_token"
        assert call_args[1]["type"] == "artist"


async def test_service_rename_station(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test rename_station service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RENAME_STATION,
            {"station_id": "123", "name": "New Name"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.rename"
        assert call_args[1]["stationId"] == "123"
        assert call_args[1]["name"] == "New Name"


async def test_service_delete_station(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test delete_station service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_DELETE_STATION,
            {"station_id": "123"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.delete"
        assert call_args[1] == "123"

