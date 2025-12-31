"""Test the Pianobar config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.pianobar.const import DEFAULT_PORT, DOMAIN


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.pianobar.config_flow.validate_input",
        return_value={"title": "Pianobar (127.0.0.1)"},
    ), patch(
        "custom_components.pianobar.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "127.0.0.1",
                CONF_PORT: 3000,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Pianobar (127.0.0.1)"
    assert result2["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 3000,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.pianobar.config_flow.validate_input",
        side_effect=Exception("Connection failed"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "127.0.0.1",
                CONF_PORT: 3000,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_already_configured(hass: HomeAssistant) -> None:
    """Test we handle already configured."""
    entry = config_entries.ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Pianobar (127.0.0.1)",
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 3000},
        source=config_entries.SOURCE_USER,
        unique_id="127.0.0.1:3000",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.pianobar.config_flow.validate_input",
        return_value={"title": "Pianobar (127.0.0.1)"},
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "127.0.0.1",
                CONF_PORT: 3000,
            },
        )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_validate_input_success(hass: HomeAssistant) -> None:
    """Test input validation with successful connection."""
    from custom_components.pianobar.config_flow import validate_input

    mock_ws = AsyncMock()
    mock_ws.close = AsyncMock()
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value.ws_connect = AsyncMock(
            return_value=mock_ws.__aenter__.return_value
        )
        
        result = await validate_input(
            hass,
            {CONF_HOST: "127.0.0.1", CONF_PORT: 3000},
        )

    assert result == {"title": "Pianobar (127.0.0.1)"}


async def test_validate_input_timeout(hass: HomeAssistant) -> None:
    """Test input validation with timeout."""
    from custom_components.pianobar.config_flow import CannotConnect, validate_input
    
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session.return_value.__aenter__.return_value.ws_connect = AsyncMock(
            side_effect=TimeoutError()
        )
        
        with pytest.raises(CannotConnect):
            await validate_input(
                hass,
                {CONF_HOST: "127.0.0.1", CONF_PORT: 3000},
            )

