"""Media player platform for Pianobar."""
from __future__ import annotations

from datetime import datetime
import logging
import math
from typing import Any

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .browse_media import async_browse_media_internal
from .const import (
    DOMAIN,
    MEDIA_TYPE_STATION,
    VOLUME_MAX_DB_DEFAULT,
    VOLUME_MIN_DB,
)
from .coordinator import PianobarCoordinator

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pianobar media player."""
    coordinator: PianobarCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PianobarMediaPlayer(coordinator, entry)])


class PianobarMediaPlayer(CoordinatorEntity[PianobarCoordinator], MediaPlayerEntity):
    """Representation of a Pianobar media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_icon = "mdi:pandora"
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_media_content_type = MediaType.MUSIC

    def __init__(self, coordinator: PianobarCoordinator, entry: ConfigEntry) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Pianobar",
            "manufacturer": "Pianobar",
            "model": "Remote Pianobar",
        }

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        if not self.coordinator.data.get("playing"):
            return MediaPlayerState.IDLE
        if self.coordinator.data.get("paused"):
            return MediaPlayerState.PAUSED
        return MediaPlayerState.PLAYING

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        db_volume = self.coordinator.data.get("volume", 0)
        max_gain = self.coordinator.data.get("maxGain", VOLUME_MAX_DB_DEFAULT)
        return self._db_to_volume_level(db_volume, max_gain)

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        return self.coordinator.data.get("station")

    @property
    def source_list(self) -> list[str] | None:
        """List of available input sources."""
        stations = self.coordinator.data.get("stations", [])
        return [station["name"] for station in stations]

    @property
    def media_content_id(self) -> str | None:
        """Content ID of current playing media."""
        return self.coordinator.data.get("stationId")

    @property
    def media_title(self) -> str | None:
        """Title of current playing media."""
        song = self.coordinator.data.get("song")
        return song.get("title") if song else None

    @property
    def media_artist(self) -> str | None:
        """Artist of current playing media."""
        song = self.coordinator.data.get("song")
        return song.get("artist") if song else None

    @property
    def media_album_name(self) -> str | None:
        """Album name of current playing media."""
        song = self.coordinator.data.get("song")
        return song.get("album") if song else None

    @property
    def media_image_url(self) -> str | None:
        """Image url of current playing media."""
        song = self.coordinator.data.get("song")
        return song.get("coverArt") if song else None

    @property
    def media_duration(self) -> int | None:
        """Duration of current playing media in seconds."""
        song = self.coordinator.data.get("song")
        return song.get("duration") if song else None

    @property
    def media_position(self) -> int | None:
        """Position of current playing media in seconds."""
        return self.coordinator.data.get("elapsed")

    @property
    def media_position_updated_at(self) -> datetime | None:
        """When the position was last updated."""
        return self.coordinator.data.get("position_updated_at")

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        stations = self.coordinator.data.get("stations", [])
        station = next((s for s in stations if s["name"] == source), None)
        
        if station:
            await self.coordinator.send_event("station.change", station["id"])
        else:
            _LOGGER.error("Station not found: %s", source)

    async def async_media_play(self) -> None:
        """Send play command."""
        await self.coordinator.send_action("playback.play")

    async def async_media_pause(self) -> None:
        """Send pause command."""
        await self.coordinator.send_action("playback.pause")

    async def async_turn_on(self) -> None:
        """Turn on the media player (resume playback)."""
        await self.coordinator.send_action("playback.play")

    async def async_turn_off(self) -> None:
        """Turn off the media player (pause, or resume if already paused)."""
        # When paused, power button should resume (PAUSED is "on" to HA cards)
        if self.coordinator.data.get("paused"):
            await self.coordinator.send_action("playback.play")
        else:
            await self.coordinator.send_action("playback.pause")

    async def async_toggle(self) -> None:
        """Toggle the media player (play/pause)."""
        await self.coordinator.send_action("playback.toggle")

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.coordinator.send_action("playback.next")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        # Convert volume level to percentage (0-100)
        volume_percent = self._volume_level_to_percent(
            volume,
            self.coordinator.data.get("maxGain", VOLUME_MAX_DB_DEFAULT),
        )
        
        await self.coordinator.send_action_with_params(
            "volume.set",
            {"volume": volume_percent}
        )

    async def async_volume_up(self) -> None:
        """Turn volume up for media player."""
        await self.coordinator.send_action("volume.up")

    async def async_volume_down(self) -> None:
        """Turn volume down for media player."""
        await self.coordinator.send_action("volume.down")

    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Play a piece of media."""
        if media_type in (MediaType.PLAYLIST, MediaType.MUSIC, MEDIA_TYPE_STATION):
            # Try to find station by ID or name
            station = self._find_station(media_id)
            
            if station:
                await self.coordinator.send_event("station.change", station["id"])
            else:
                _LOGGER.error("Station not found: %s", media_id)

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        return await async_browse_media_internal(
            self.hass,
            self.coordinator,
            media_content_type,
            media_content_id,
        )

    def _find_station(self, station_id_or_name: str) -> dict[str, Any] | None:
        """Find a station by ID or name."""
        stations = self.coordinator.data.get("stations", [])
        
        # Try to find by ID first
        station = next((s for s in stations if s["id"] == station_id_or_name), None)
        if station:
            return station
            
        # Try to find by name
        return next((s for s in stations if s["name"] == station_id_or_name), None)

    @staticmethod
    def _db_to_volume_level(db: float, max_gain: float = VOLUME_MAX_DB_DEFAULT) -> float:
        """Convert dB to volume level (0.0-1.0) using perceptual curve."""
        if db <= 0:
            # -40 to 0 dB maps to 0-50%
            normalized = 1 - math.sqrt(abs(db) / abs(VOLUME_MIN_DB))
            slider_percent = normalized * 50
        else:
            # 0 to maxGain maps to 50-100%
            normalized = db / max_gain
            slider_percent = 50 + normalized * 50
            
        return slider_percent / 100.0

    @staticmethod
    def _volume_level_to_percent(
        volume_level: float,
        max_gain: float = VOLUME_MAX_DB_DEFAULT,
    ) -> float:
        """Convert volume level (0.0-1.0) to percentage for API (0-100)."""
        # This is used directly by the API, which expects 0-100
        return volume_level * 100.0

    @staticmethod
    def _volume_level_to_db(
        volume_level: float,
        max_gain: float = VOLUME_MAX_DB_DEFAULT,
    ) -> float:
        """Convert volume level (0.0-1.0) to dB."""
        slider_percent = volume_level * 100
        
        if slider_percent <= 50:
            # Bottom half: -40 to 0 dB (quadratic curve)
            normalized = slider_percent / 50
            return VOLUME_MIN_DB * (1 - normalized) ** 2
        else:
            # Top half: 0 to maxGain dB (linear)
            normalized = (slider_percent - 50) / 50
            return max_gain * normalized

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

