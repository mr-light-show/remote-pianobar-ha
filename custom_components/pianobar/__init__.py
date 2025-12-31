"""The Pianobar integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_BAN_SONG,
    SERVICE_CREATE_STATION,
    SERVICE_DELETE_STATION,
    SERVICE_LOVE_SONG,
    SERVICE_RENAME_STATION,
    SERVICE_TIRED_OF_SONG,
)
from .coordinator import PianobarCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pianobar from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    coordinator = PianobarCoordinator(hass, host, port)

    try:
        await coordinator.async_connect()
    except Exception as err:
        _LOGGER.error("Failed to connect to Pianobar: %s", err)
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Reload entry when options change (host/port updated)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_love_song(call: ServiceCall) -> None:
        """Handle love_song service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("song.love")

    async def async_ban_song(call: ServiceCall) -> None:
        """Handle ban_song service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("song.ban")

    async def async_tired_of_song(call: ServiceCall) -> None:
        """Handle tired_of_song service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("song.tired")

    async def async_create_station(call: ServiceCall) -> None:
        """Handle create_station service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_type = call.data.get("type", "song")
        track_token = coordinator.data.get("song", {}).get("trackToken")
        
        if not track_token:
            _LOGGER.error("No track token available")
            return
            
        await coordinator.send_event(
            "station.createFrom",
            {"trackToken": track_token, "type": station_type}
        )

    async def async_rename_station(call: ServiceCall) -> None:
        """Handle rename_station service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        new_name = call.data.get("name")
        
        await coordinator.send_event(
            "station.rename",
            {"stationId": station_id, "name": new_name}
        )

    async def async_delete_station(call: ServiceCall) -> None:
        """Handle delete_station service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.delete",
            station_id
        )

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOVE_SONG,
        async_love_song,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_BAN_SONG,
        async_ban_song,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TIRED_OF_SONG,
        async_tired_of_song,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_STATION,
        async_create_station,
        schema=vol.Schema({
            vol.Optional("type", default="song"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENAME_STATION,
        async_rename_station,
        schema=vol.Schema({
            vol.Required("station_id"): cv.string,
            vol.Required("name"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_STATION,
        async_delete_station,
        schema=vol.Schema({
            vol.Required("station_id"): cv.string,
        }),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: PianobarCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)

