"""Coordinator for Pianobar integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    WS_CONNECT_TIMEOUT,
    WS_MAX_RECONNECT_DELAY,
    WS_RECONNECT_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class PianobarCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Pianobar data from WebSocket."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.host = host
        self.port = port
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._listen_task: asyncio.Task | None = None
        self._reconnect_delay = WS_RECONNECT_DELAY
        self._is_closing = False
        
        # State data
        self.data: dict[str, Any] = {
            "playing": False,
            "paused": False,
            "volume": 0,
            "maxGain": 10,
            "station": "",
            "stationId": "",
            "stations": [],
        }

    async def async_connect(self) -> None:
        """Connect to the WebSocket."""
        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = f"ws://{self.host}:{self.port}/socket.io"
        
        try:
            _LOGGER.debug("Connecting to %s", url)
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(
                    url,
                    protocols=["socketio"],
                    heartbeat=30,
                ),
                timeout=WS_CONNECT_TIMEOUT,
            )
            _LOGGER.info("Connected to Pianobar at %s:%s", self.host, self.port)
            
            # Reset reconnect delay on successful connection
            self._reconnect_delay = WS_RECONNECT_DELAY
            
            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen())
            
            # Request initial state
            await self.send_event("query", None)
            
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to Pianobar")
            raise ConnectionError("Connection timeout") from err
        except Exception as err:
            _LOGGER.error("Error connecting to Pianobar: %s", err)
            raise ConnectionError(f"Connection error: {err}") from err

    async def async_disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._is_closing = True
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
            
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
        
        if self._ws and not self._ws.closed:
            await self._ws.close()
            self._ws = None
            
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _listen(self) -> None:
        """Listen for WebSocket messages."""
        if not self._ws:
            return
            
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._handle_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error("WebSocket error: %s", self._ws.exception())
                    break
                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                    _LOGGER.warning("WebSocket closed")
                    break
                    
        except Exception as err:
            _LOGGER.error("Error in WebSocket listener: %s", err)
        finally:
            if not self._is_closing:
                _LOGGER.warning("WebSocket connection lost, attempting to reconnect")
                # Clear playback state on connection loss so player cards reset
                self._clear_playback_state()
                self.async_set_updated_data(self.data)
                self._reconnect_task = asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Reconnect to the WebSocket with exponential backoff."""
        while not self._is_closing:
            await asyncio.sleep(self._reconnect_delay)
            
            try:
                await self.async_connect()
                _LOGGER.info("Reconnected to Pianobar")
                return
            except Exception as err:
                _LOGGER.warning(
                    "Reconnect failed, retrying in %s seconds: %s",
                    self._reconnect_delay,
                    err,
                )
                # Exponential backoff
                self._reconnect_delay = min(
                    self._reconnect_delay * 2, WS_MAX_RECONNECT_DELAY
                )

    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket message."""
        # Socket.IO messages start with packet type "2" for EVENT
        if not message.startswith("2"):
            return
            
        try:
            # Remove packet type prefix and parse JSON
            json_str = message[1:]
            event_data = json.loads(json_str)
            
            if not isinstance(event_data, list) or len(event_data) < 2:
                return
                
            event_name = event_data[0]
            event_payload = event_data[1]
            
            _LOGGER.debug("Received event: %s", event_name)
            
            # Handle different event types
            if event_name == "process":
                self._handle_process_event(event_payload)
            elif event_name == "start":
                self._handle_start_event(event_payload)
            elif event_name == "stop":
                self._handle_stop_event()
            elif event_name == "stopped":
                self._handle_stopped_event(event_payload)
            elif event_name == "progress":
                self._handle_progress_event(event_payload)
            elif event_name == "volume":
                self._handle_volume_event(event_payload)
            elif event_name == "playState":
                self._handle_play_state_event(event_payload)
            elif event_name == "stations":
                self._handle_stations_event(event_payload)
                
            # Notify listeners of state change
            self.async_set_updated_data(self.data)
            
        except json.JSONDecodeError as err:
            _LOGGER.error("Failed to parse message: %s", err)
        except Exception as err:
            _LOGGER.error("Error handling message: %s", err)

    def _handle_process_event(self, payload: dict[str, Any]) -> None:
        """Handle process event (full state update)."""
        # Wire protocol sends volume as 0-100, HA expects 0.0-1.0
        wire_volume = payload.get("volume", 0)
        self.data.update({
            "playing": payload.get("playing", False),
            "paused": payload.get("paused", False),
            "volume": wire_volume / 100.0,
            "maxGain": payload.get("maxGain", 10),
            "station": payload.get("station", ""),
            "stationId": payload.get("stationId", ""),
        })
        
        if payload.get("playing") and "song" in payload:
            self.data["song"] = payload["song"]
            if "elapsed" in payload:
                self.data["elapsed"] = payload["elapsed"]
                self.data["position_updated_at"] = dt_util.utcnow()

    def _handle_start_event(self, payload: dict[str, Any]) -> None:
        """Handle start event (new song started)."""
        self.data.update({
            "playing": True,
            "paused": False,
            "song": payload,
            "elapsed": 0,
            "position_updated_at": dt_util.utcnow(),
            "station": payload.get("station", ""),
            "stationId": payload.get("stationId", ""),
        })

    def _handle_stop_event(self) -> None:
        """Handle stop event (song ended/skipped)."""
        self.data["playing"] = False
        if "song" in self.data:
            del self.data["song"]
        if "elapsed" in self.data:
            del self.data["elapsed"]

    def _handle_stopped_event(self, payload: dict[str, Any]) -> None:
        """Handle stopped event - fully disconnected from Pandora."""
        self._clear_playback_state()

    def _handle_progress_event(self, payload: dict[str, Any]) -> None:
        """Handle progress event (playback position update)."""
        if self.data.get("playing"):
            self.data["elapsed"] = payload.get("elapsed", 0)
            self.data["position_updated_at"] = dt_util.utcnow()

    def _handle_volume_event(self, payload: float) -> None:
        """Handle volume event (volume changed)."""
        # Wire protocol sends 0-100, HA expects 0.0-1.0
        self.data["volume"] = payload / 100.0

    def _handle_play_state_event(self, payload: dict[str, Any]) -> None:
        """Handle playState event (pause/resume)."""
        self.data["paused"] = payload.get("paused", False)

    def _handle_stations_event(self, payload: list[dict[str, Any]]) -> None:
        """Handle stations event (station list update)."""
        self.data["stations"] = payload

    def _clear_playback_state(self) -> None:
        """Clear playback state (used on disconnect/stopped)."""
        self.data.update({
            "playing": False,
            "paused": False,
            "station": None,
            "stationId": None,
        })
        # Remove optional keys
        for key in ("song", "elapsed", "position_updated_at"):
            self.data.pop(key, None)

    async def send_event(self, event_name: str, payload: Any) -> None:
        """Send an event to the WebSocket."""
        if not self._ws or self._ws.closed:
            _LOGGER.error("WebSocket not connected")
            return
            
        try:
            # Format as Socket.IO EVENT message
            message = f'2["{event_name}",{json.dumps(payload)}]'
            await self._ws.send_str(message)
            _LOGGER.debug("Sent event: %s", event_name)
        except Exception as err:
            _LOGGER.error("Error sending event %s: %s", event_name, err)

    async def send_action(self, action: str) -> None:
        """Send an action command."""
        await self.send_event("action", action)

    async def send_action_with_params(self, action: str, params: dict[str, Any]) -> None:
        """Send an action command with parameters."""
        payload = {"action": action}
        payload.update(params)
        await self.send_event("action", payload)

