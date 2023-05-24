"""Handler for Sonos websockets."""
import asyncio
import logging
import sys
from typing import Any, cast

import aiohttp
from aiohttp import WSMsgType

from .const import API_KEY, MAX_ATTEMPTS
from .exception import (
    SonosWebsocketError,
    SonosWSConnectionError,
    Unauthorized,
    Unsupported,
)

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout
else:
    from asyncio import timeout as asyncio_timeout


_LOGGER = logging.getLogger(__name__)


class SonosWebsocket:
    """Sonos websocket handler."""

    def __init__(
        self,
        ip_addr: str,
        player_id: str | None = None,
        household_id: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize the websocket instance."""
        self.uri = f"wss://{ip_addr}:1443/websocket/api"
        self._own_session = not session
        self.session = session or aiohttp.ClientSession()
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self._household_id = household_id
        self._player_id = player_id
        self._connect_lock = asyncio.Lock()

    async def connect(self) -> None:
        """Open a persistent websocket connection and act on events."""
        async with self._connect_lock:
            if self.ws and not self.ws.closed:
                _LOGGER.warning("Websocket is already connected")
                return

        _LOGGER.debug("Opening websocket to %s", self.uri)
        headers = {
            "X-Sonos-Api-Key": API_KEY,
            "Sec-WebSocket-Protocol": "v1.api.smartspeaker.audio",
        }
        try:
            async with asyncio_timeout(3):
                self.ws = await self.session.ws_connect(
                    self.uri, headers=headers, verify_ssl=False
                )
        except aiohttp.ClientResponseError as exc:
            if exc.code == 401:
                _LOGGER.error("Credentials rejected: %s", exc)
                raise Unauthorized("Credentials rejected") from exc
            raise SonosWSConnectionError(
                f"Unexpected response received: {exc}"
            ) from exc
        except aiohttp.ClientConnectionError as exc:
            raise SonosWSConnectionError(f"Connection error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise SonosWSConnectionError("Connection timed out") from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise SonosWSConnectionError(f"Unknown error: {exc}") from exc
        _LOGGER.debug("Successfully connected to %s", self.uri)

    async def close(self):
        """Close the websocket connection."""
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self._own_session and self.session and not self.session.closed:
            await self.session.close()

    async def send_command(
        self, command: dict[str, Any], options: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Send commands over the websocket and handle their responses."""
        attempt = 1
        while attempt <= MAX_ATTEMPTS:
            if not self.ws or self.ws.closed:
                await self.connect()
                assert self.ws

            payload = [command, options or {}]
            _LOGGER.debug("Sending command: %s", payload)
            try:
                async with asyncio_timeout(3):
                    await self.ws.send_json(payload)
                    msg = await self.ws.receive()
            except asyncio.TimeoutError:
                _LOGGER.error("Command timed out")
            except ConnectionResetError:
                # Websocket closing
                self.ws = None
                _LOGGER.debug("Websocket connection reset, will try again")
            else:
                if msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
                    _LOGGER.debug("Websocket closed, will try again")
                elif msg.type != WSMsgType.TEXT:
                    _LOGGER.error("Received non-text message: %s", msg.type.name)
                else:
                    return msg.json()
            attempt += 1

        command_name = command.get("command", "Empty")
        raise SonosWebsocketError(
            f"{command_name} command failed after {MAX_ATTEMPTS} attempts"
        )

    async def play_clip(
        self, uri: str, volume: int | None = None
    ) -> list[dict[str, Any]]:
        """Play an audio clip."""
        command = {
            "namespace": "audioClip:1",
            "command": "loadAudioClip",
            "playerId": await self.get_player_id(),
        }
        options: dict[str, Any] = {
            "name": "Sonos Websocket",
            "appId": "com.jjlawren.sonos_websocket",
            "streamUrl": uri,
        }
        if volume:
            options["volume"] = volume
        return await self.send_command(command, options)

    async def get_household_id(self) -> str:
        """Get the household ID of this device.

        Note: This is an invalid command but returns the household ID anyway.
        """
        if self._household_id:
            return self._household_id
        response, _ = await self.send_command({})
        if household_id := response.get("householdId"):
            self._household_id = household_id
            return household_id
        raise SonosWebsocketError("Could not determine household ID")

    async def get_groups(self) -> list[dict[str, Any]]:
        """Return the current group and player configuration."""
        command = {
            "namespace": "groups:1",
            "command": "getGroups",
            "householdId": await self.get_household_id(),
        }
        return await self.send_command(command)

    async def get_player_id(self) -> str:
        """Retrieve the player identifier for this speaker."""
        if self._player_id:
            return self._player_id
        response, data = await self.get_groups()
        if not response["success"]:
            raise SonosWebsocketError(f"Retrieving group data failed: {data}")
        if player := next(
            (p for p in data["players"] if p["websocketUrl"] == self.uri), None
        ):
            if "AUDIO_CLIP" not in player["capabilities"]:
                raise Unsupported("Device does not support AUDIO_CLIP")
            self._player_id = cast(str, player["id"])
            return self._player_id
        raise SonosWebsocketError("No matching player found in group data")
