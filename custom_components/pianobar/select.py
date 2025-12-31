"""Select platform for Pianobar integration."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PianobarCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pianobar select entity."""
    coordinator: PianobarCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PianobarStationSelect(coordinator, entry)])


class PianobarStationSelect(CoordinatorEntity[PianobarCoordinator], SelectEntity):
    """Select entity for Pianobar station selection."""

    _attr_has_entity_name = True
    _attr_name = "Station"
    _attr_icon = "mdi:radio"

    def __init__(
        self,
        coordinator: PianobarCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_station_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Pianobar",
            "manufacturer": "Pandora",
            "model": "Pianobar",
        }

    @property
    def options(self) -> list[str]:
        """Return list of station names."""
        stations = self.coordinator.data.get("stations", [])
        return [station["name"] for station in stations]

    @property
    def current_option(self) -> str | None:
        """Return the currently selected station."""
        station = self.coordinator.data.get("station")
        if station and station in self.options:
            return station
        return None

    async def async_select_option(self, option: str) -> None:
        """Change to the selected station."""
        stations = self.coordinator.data.get("stations", [])
        for station in stations:
            if station["name"] == option:
                await self.coordinator.send_event("station.change", station["id"])
                _LOGGER.debug("Changed station to: %s (ID: %s)", option, station["id"])
                break

