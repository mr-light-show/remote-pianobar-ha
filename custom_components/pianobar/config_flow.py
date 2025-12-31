"""Config flow for Pianobar integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN, WS_CONNECT_TIMEOUT

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    
    # Test the WebSocket connection
    url = f"ws://{host}:{port}/socket.io"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(WS_CONNECT_TIMEOUT):
                async with session.ws_connect(
                    url,
                    protocols=["socketio"],
                ) as ws:
                    # Connection successful, close it
                    await ws.close()
                    
    except asyncio.TimeoutError as err:
        raise CannotConnect("Connection timeout") from err
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection failed: {err}") from err
    except Exception as err:
        raise CannotConnect(f"Unexpected error: {err}") from err

    # Return info that you want to store in the config entry.
    return {"title": f"{DEFAULT_NAME} ({host})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pianobar."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on host and port
                await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Pianobar."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Update the config entry with new data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=user_input,
                    title=f"{DEFAULT_NAME} ({user_input[CONF_HOST]})",
                )
                return self.async_create_entry(title="", data={})

        # Pre-fill with current values
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST, default=self.config_entry.data.get(CONF_HOST, "")
                ): str,
                vol.Required(
                    CONF_PORT, default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
                ): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
