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
from .coordinator import PianobarCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SELECT]


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
            {"stationId": station_id, "newName": new_name}
        )

    async def async_delete_station(call: ServiceCall) -> None:
        """Handle delete_station service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.delete",
            station_id
        )

    async def async_reconnect(call: ServiceCall) -> None:
        """Handle reconnect service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        if not coordinator.is_connected:
            try:
                await coordinator.async_connect()
                _LOGGER.info("Reconnected to Pianobar")
            except Exception as err:
                _LOGGER.error("Failed to reconnect: %s", err)
        else:
            _LOGGER.info("Already connected to Pianobar")

    async def async_explain_song(call: ServiceCall) -> dict[str, Any]:
        """Handle explain_song service call."""
        _LOGGER.debug("explain_song service called")
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("song.explain")
        explanation = await coordinator.wait_for_response("song_explanation")
        _LOGGER.debug("Got explanation: %s", explanation)
        return {"explanation": explanation or ""}

    async def async_get_upcoming(call: ServiceCall) -> dict[str, Any]:
        """Handle get_upcoming service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("query.upcoming")
        upcoming = await coordinator.wait_for_response("upcoming")
        return {"songs": upcoming or []}

    async def async_set_quick_mix(call: ServiceCall) -> None:
        """Handle set_quick_mix service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_ids = call.data.get("station_ids", [])
        await coordinator.send_event("station.setQuickMix", station_ids)

    async def async_add_seed(call: ServiceCall) -> None:
        """Handle add_seed service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        music_id = call.data.get("music_id")
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.addMusic",
            {"musicId": music_id, "stationId": station_id}
        )

    async def async_get_station_info(call: ServiceCall) -> dict[str, Any]:
        """Handle get_station_info service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.getInfo",
            {"stationId": station_id}
        )
        station_info = await coordinator.wait_for_response("station_info")
        return station_info or {}

    async def async_delete_seed(call: ServiceCall) -> None:
        """Handle delete_seed service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        seed_id = call.data.get("seed_id")
        seed_type = call.data.get("seed_type")
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.deleteSeed",
            {"seedId": seed_id, "seedType": seed_type, "stationId": station_id}
        )

    async def async_delete_feedback(call: ServiceCall) -> None:
        """Handle delete_feedback service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        feedback_id = call.data.get("feedback_id")
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.deleteFeedback",
            {"feedbackId": feedback_id, "stationId": station_id}
        )

    async def async_get_station_modes(call: ServiceCall) -> dict[str, Any]:
        """Handle get_station_modes service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.getModes",
            {"stationId": station_id}
        )
        modes = await coordinator.wait_for_response("station_modes")
        return {"modes": modes or []}

    async def async_set_station_mode(call: ServiceCall) -> None:
        """Handle set_station_mode service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        mode_id = call.data.get("mode_id")
        
        await coordinator.send_event(
            "station.setMode",
            {"stationId": station_id, "modeId": mode_id}
        )

    async def async_toggle_playback(call: ServiceCall) -> None:
        """Handle toggle_playback service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("playback.toggle")

    async def async_reset_volume(call: ServiceCall) -> None:
        """Handle reset_volume service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.send_action("volume.reset")

    async def async_search(call: ServiceCall) -> dict[str, Any]:
        """Handle search service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        query = call.data.get("query")
        
        await coordinator.send_event(
            "music.search",
            {"query": query}
        )
        search_results = await coordinator.wait_for_response("search_results")
        return search_results or {"categories": []}

    async def async_get_genres(call: ServiceCall) -> dict[str, Any]:
        """Handle get_genres service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        
        await coordinator.send_event(
            "station.getGenres",
            {}
        )
        genres = await coordinator.wait_for_response("genres")
        return genres or {"categories": []}

    async def async_create_station_from_music_id(call: ServiceCall) -> None:
        """Handle create_station_from_music_id service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        music_id = call.data.get("music_id")
        
        await coordinator.send_event(
            "station.addGenre",
            {"musicId": music_id}
        )

    async def async_add_shared_station(call: ServiceCall) -> None:
        """Handle add_shared_station service call."""
        coordinator = hass.data[DOMAIN][entry.entry_id]
        station_id = call.data.get("station_id")
        
        await coordinator.send_event(
            "station.addShared",
            {"stationId": station_id}
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECONNECT,
        async_reconnect,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPLAIN_SONG,
        async_explain_song,
        schema=vol.Schema({}),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_UPCOMING,
        async_get_upcoming,
        schema=vol.Schema({}),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_QUICK_MIX,
        async_set_quick_mix,
        schema=vol.Schema({
            vol.Required("station_ids"): [cv.string],
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_SEED,
        async_add_seed,
        schema=vol.Schema({
            vol.Required("music_id"): cv.string,
            vol.Required("station_id"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_STATION_INFO,
        async_get_station_info,
        schema=vol.Schema({
            vol.Required("station_id"): cv.string,
        }),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_SEED,
        async_delete_seed,
        schema=vol.Schema({
            vol.Required("seed_id"): cv.string,
            vol.Required("seed_type"): vol.In(["artist", "song", "station"]),
            vol.Required("station_id"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_FEEDBACK,
        async_delete_feedback,
        schema=vol.Schema({
            vol.Required("feedback_id"): cv.string,
            vol.Required("station_id"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_STATION_MODES,
        async_get_station_modes,
        schema=vol.Schema({
            vol.Required("station_id"): cv.string,
        }),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_STATION_MODE,
        async_set_station_mode,
        schema=vol.Schema({
            vol.Required("station_id"): cv.string,
            vol.Required("mode_id"): vol.Coerce(int),
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_PLAYBACK,
        async_toggle_playback,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_VOLUME,
        async_reset_volume,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH,
        async_search,
        schema=vol.Schema({
            vol.Required("query"): cv.string,
        }),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_GENRES,
        async_get_genres,
        schema=vol.Schema({}),
        supports_response="optional",
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_STATION_FROM_MUSIC_ID,
        async_create_station_from_music_id,
        schema=vol.Schema({
            vol.Required("music_id"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_SHARED_STATION,
        async_add_shared_station,
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

