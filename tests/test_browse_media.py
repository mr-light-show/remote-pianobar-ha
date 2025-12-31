"""Test the Pianobar browse media."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from homeassistant.components.media_player import MediaClass
from homeassistant.core import HomeAssistant

from custom_components.pianobar.browse_media import async_browse_media_internal
from custom_components.pianobar.const import MEDIA_TYPE_STATION, MEDIA_TYPE_STATIONS


async def test_browse_media_root(hass: HomeAssistant, mock_coordinator) -> None:
    """Test browsing root level."""
    result = await async_browse_media_internal(
        hass,
        mock_coordinator,
        None,
        None,
    )
    
    assert result.title == "Pandora"
    assert result.media_class == MediaClass.DIRECTORY
    assert result.can_play is False
    assert result.can_expand is True
    assert len(result.children) == 1
    assert result.children[0].title == "My Stations"


async def test_browse_media_stations(
    hass: HomeAssistant,
    mock_coordinator,
    mock_station_data,
) -> None:
    """Test browsing stations."""
    mock_coordinator.data = {"stations": mock_station_data}
    
    result = await async_browse_media_internal(
        hass,
        mock_coordinator,
        MEDIA_TYPE_STATIONS,
        MEDIA_TYPE_STATIONS,
    )
    
    assert result.title == "My Stations"
    assert result.media_class == MediaClass.DIRECTORY
    assert result.can_play is False
    assert result.can_expand is True
    assert len(result.children) == 3
    
    # Check first station
    assert result.children[0].title == "Test Station 1"
    assert result.children[0].media_content_id == "123456789"
    assert result.children[0].media_content_type == MEDIA_TYPE_STATION
    assert result.children[0].media_class == MediaClass.PLAYLIST
    assert result.children[0].can_play is True
    assert result.children[0].can_expand is False


async def test_browse_media_empty_stations(
    hass: HomeAssistant,
    mock_coordinator,
) -> None:
    """Test browsing with no stations."""
    mock_coordinator.data = {"stations": []}
    
    result = await async_browse_media_internal(
        hass,
        mock_coordinator,
        MEDIA_TYPE_STATIONS,
        MEDIA_TYPE_STATIONS,
    )
    
    assert result.title == "My Stations"
    assert len(result.children) == 0


async def test_browse_media_invalid_type(
    hass: HomeAssistant,
    mock_coordinator,
) -> None:
    """Test browsing with invalid media type."""
    result = await async_browse_media_internal(
        hass,
        mock_coordinator,
        "invalid_type",
        "invalid_id",
    )
    
    # Should fall back to root
    assert result.title == "Pandora"
    assert result.media_class == MediaClass.DIRECTORY

