"""Test the Pianobar integration init."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.pianobar.const import (
    DOMAIN,
    SERVICE_ADD_SEED,
    SERVICE_ADD_SHARED_STATION,
    SERVICE_BAN_SONG,
    SERVICE_CREATE_STATION,
    SERVICE_CREATE_STATION_FROM_MUSIC_ID,
    SERVICE_DELETE_FEEDBACK,
    SERVICE_DELETE_SEED,
    SERVICE_DELETE_STATION,
    SERVICE_EXPLAIN_SONG,
    SERVICE_GET_GENRES,
    SERVICE_GET_STATION_INFO,
    SERVICE_GET_STATION_MODES,
    SERVICE_GET_UPCOMING,
    SERVICE_LOVE_SONG,
    SERVICE_RECONNECT,
    SERVICE_RENAME_STATION,
    SERVICE_RESET_VOLUME,
    SERVICE_SEARCH,
    SERVICE_SET_QUICK_MIX,
    SERVICE_SET_STATION_MODE,
    SERVICE_TIRED_OF_SONG,
    SERVICE_TOGGLE_PLAYBACK,
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


async def test_service_tired_of_song(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test tired_of_song service."""
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
            SERVICE_TIRED_OF_SONG,
            {},
            blocking=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("song.tired")


async def test_service_reconnect(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test reconnect service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.is_connected = False
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECONNECT,
            {},
            blocking=True,
        )
        
        # Should call async_connect when not connected
        assert mock_coordinator.async_connect.call_count == 2  # Once during setup, once for reconnect


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
        assert call_args[1]["newName"] == "New Name"


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


async def test_service_explain_song(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test explain_song service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_action = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(return_value="Test explanation")
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_EXPLAIN_SONG,
            {},
            blocking=True,
            return_response=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("song.explain")
        assert response["explanation"] == "Test explanation"


async def test_service_get_upcoming(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test get_upcoming service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_action = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(return_value=[{"title": "Test Song"}])
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_UPCOMING,
            {},
            blocking=True,
            return_response=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("query.upcoming")
        assert len(response["songs"]) == 1


async def test_service_set_quick_mix(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test set_quick_mix service."""
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
            SERVICE_SET_QUICK_MIX,
            {"station_ids": ["123", "456"]},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once_with(
            "station.setQuickMix", ["123", "456"]
        )


async def test_service_add_seed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test add_seed service."""
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
            SERVICE_ADD_SEED,
            {"music_id": "M123", "station_id": "S456"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.addMusic"
        assert call_args[1]["musicId"] == "M123"
        assert call_args[1]["stationId"] == "S456"


async def test_service_get_station_info(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test get_station_info service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(
            return_value={"artistSeeds": [], "songSeeds": []}
        )
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_STATION_INFO,
            {"station_id": "123"},
            blocking=True,
            return_response=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        assert "artistSeeds" in response


async def test_service_delete_seed(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test delete_seed service."""
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
            SERVICE_DELETE_SEED,
            {"seed_id": "AS123", "seed_type": "artist", "station_id": "S456"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.deleteSeed"


async def test_service_delete_feedback(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test delete_feedback service."""
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
            SERVICE_DELETE_FEEDBACK,
            {"feedback_id": "FB123", "station_id": "S456"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.deleteFeedback"


async def test_service_get_station_modes(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test get_station_modes service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(return_value=[{"id": 0, "name": "My Station"}])
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_STATION_MODES,
            {"station_id": "123"},
            blocking=True,
            return_response=True,
        )
        
        assert len(response["modes"]) == 1


async def test_service_set_station_mode(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test set_station_mode service."""
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
            SERVICE_SET_STATION_MODE,
            {"station_id": "123", "mode_id": 2},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.setMode"
        assert call_args[1]["modeId"] == 2


async def test_service_toggle_playback(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test toggle_playback service."""
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
            SERVICE_TOGGLE_PLAYBACK,
            {},
            blocking=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("playback.toggle")


async def test_service_reset_volume(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test reset_volume service."""
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
            SERVICE_RESET_VOLUME,
            {},
            blocking=True,
        )
        
        mock_coordinator.send_action.assert_called_once_with("volume.reset")


async def test_service_search(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test search service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(
            return_value={
                "categories": [
                    {
                        "name": "Artists",
                        "results": [{"name": "Test Artist", "musicId": "R123"}]
                    }
                ]
            }
        )
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_SEARCH,
            {"query": "Test Artist"},
            blocking=True,
            return_response=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "music.search"
        assert call_args[1]["query"] == "Test Artist"
        assert "categories" in response
        assert len(response["categories"]) == 1


async def test_service_get_genres(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test get_genres service."""
    mock_config_entry.add_to_hass(hass)
    
    with patch(
        "custom_components.pianobar.PianobarCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = mock_coordinator_class.return_value
        mock_coordinator.async_connect = AsyncMock()
        mock_coordinator.send_event = AsyncMock()
        mock_coordinator.wait_for_response = AsyncMock(
            return_value={
                "categories": [
                    {
                        "name": "Rock",
                        "genres": [{"name": "Classic Rock", "musicId": "G100"}]
                    }
                ]
            }
        )
        mock_coordinator.data = {"playing": False}
        
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        response = await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_GENRES,
            {},
            blocking=True,
            return_response=True,
        )
        
        mock_coordinator.send_event.assert_called_once_with("station.getGenres", {})
        assert "categories" in response
        assert len(response["categories"]) == 1


async def test_service_create_station_from_music_id(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test create_station_from_music_id service."""
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
            SERVICE_CREATE_STATION_FROM_MUSIC_ID,
            {"music_id": "G100"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.addGenre"
        assert call_args[1]["musicId"] == "G100"


async def test_service_add_shared_station(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test add_shared_station service."""
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
            SERVICE_ADD_SHARED_STATION,
            {"station_id": "1234567890"},
            blocking=True,
        )
        
        mock_coordinator.send_event.assert_called_once()
        call_args = mock_coordinator.send_event.call_args[0]
        assert call_args[0] == "station.addShared"
        assert call_args[1]["stationId"] == "1234567890"

