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
    """Set up the Pianobar select entities."""
    coordinator: PianobarCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [PianobarStationSelect(coordinator, entry)]

    # Only add account select when multiple accounts are configured
    accounts = coordinator.data.get("accounts", [])
    if len(accounts) > 1:
        entities.append(PianobarAccountSelect(coordinator, entry))

    async_add_entities(entities)


class PianobarStationSelect(CoordinatorEntity[PianobarCoordinator], SelectEntity):
    """Select entity for Pianobar station selection."""

    _attr_has_entity_name = True
    _attr_translation_key = "station"
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
            "translation_key": "pianobar_device",
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


class PianobarAccountSelect(CoordinatorEntity[PianobarCoordinator], SelectEntity):
    """Select entity for Pianobar account switching."""

    _attr_has_entity_name = True
    _attr_translation_key = "account"
    _attr_icon = "mdi:account-switch"

    def __init__(
        self,
        coordinator: PianobarCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the account select entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_account_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "translation_key": "pianobar_device",
            "manufacturer": "Pandora",
            "model": "Pianobar",
        }

    @property
    def options(self) -> list[str]:
        """Return list of account labels."""
        accounts = self.coordinator.data.get("accounts", [])
        return [acct["label"] for acct in accounts]

    @property
    def current_option(self) -> str | None:
        """Return the currently active account label."""
        current = self.coordinator.data.get("current_account")
        if current:
            label = current.get("label", current.get("id", ""))
            if label in self.options:
                return label
        return None

    async def async_select_option(self, option: str) -> None:
        """Switch to the selected account."""
        accounts = self.coordinator.data.get("accounts", [])
        for acct in accounts:
            if acct["label"] == option:
                await self.coordinator.send_action_with_params(
                    "app.pandora-reconnect", {"account_id": acct["id"]}
                )
                _LOGGER.debug("Switching to account: %s (ID: %s)", option, acct["id"])
                break

