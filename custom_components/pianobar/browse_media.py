"""Browse media helper for Pianobar."""
from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    BrowseMedia,
    MediaClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation

from .const import DOMAIN, MEDIA_TYPE_STATION
from .coordinator import PianobarCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_browse_media_internal(
    hass: HomeAssistant,
    coordinator: PianobarCoordinator,
    media_content_type: str | None,
    media_content_id: str | None,
) -> BrowseMedia:
    """Browse media."""
    # Use category "common" — hassfest allows slug keys under "common" only; a custom
    # "browse_media" block in translations/en.json is rejected (see hassfest gen_strings_schema).
    translations = await translation.async_get_translations(
        hass, hass.config.language, "common", integrations=[DOMAIN]
    )
    prefix = f"component.{DOMAIN}.common."

    def _title(key: str, default: str) -> str:
        return translations.get(f"{prefix}{key}", default)

    my_stations = _title("browse_media_my_stations", "My Stations")
    unknown_station = _title("browse_media_unknown_station", "Unknown Station")

    # Root level - return all stations
    if media_content_id is None or media_content_id in ("", "root", "stations"):
        return _build_stations_browse(coordinator, my_stations)

    # Specific station requested - return it with empty children
    # (Pandora stations don't have browsable sub-content)
    if media_content_type in (MEDIA_TYPE_STATION, "playlist"):
        return _build_station_browse(
            coordinator, media_content_id, unknown_station
        )

    # Default to root
    return _build_stations_browse(coordinator, my_stations)


def _build_stations_browse(
    coordinator: PianobarCoordinator, root_title: str
) -> BrowseMedia:
    """Build stations browse structure - flat list at root level."""
    stations = coordinator.data.get("stations", [])

    children = [
        BrowseMedia(
            media_class=MediaClass.PLAYLIST,
            media_content_id=station["id"],
            media_content_type=MEDIA_TYPE_STATION,
            title=station["name"],
            can_play=True,
            can_expand=False,
            thumbnail=None,
        )
        for station in stations
    ]

    return BrowseMedia(
        media_class=MediaClass.DIRECTORY,
        media_content_id="stations",
        media_content_type="stations",
        title=root_title,
        can_play=False,
        can_expand=True,
        children=children,
    )


def _build_station_browse(
    coordinator: PianobarCoordinator, station_id: str, unknown_title: str
) -> BrowseMedia:
    """Build browse structure for a single station (no children - stations are leaf nodes)."""
    stations = coordinator.data.get("stations", [])

    # Find station by ID or name
    for station in stations:
        if station["id"] == station_id or station["name"] == station_id:
            return BrowseMedia(
                media_class=MediaClass.PLAYLIST,
                media_content_id=station["id"],
                media_content_type=MEDIA_TYPE_STATION,
                title=station["name"],
                can_play=True,
                can_expand=False,
                children=[],  # Empty - Pandora stations don't have browsable content
                thumbnail=None,
            )

    # Station not found - return empty placeholder
    return BrowseMedia(
        media_class=MediaClass.PLAYLIST,
        media_content_id=station_id,
        media_content_type=MEDIA_TYPE_STATION,
        title=unknown_title,
        can_play=False,
        can_expand=False,
        children=[],
    )
