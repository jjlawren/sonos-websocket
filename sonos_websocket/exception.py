"""Exceptions used by sonos_websocket."""


class SonosWebsocketError(Exception):
    """Base exception for Sonos websockets."""


class SonosWSConnectionError(SonosWebsocketError):
    """Connection error encountered on a Sonos websocket."""


class Unauthorized(SonosWebsocketError):
    """Authorization rejected when connecting to a Sonos websocket."""


class Unsupported(SonosWebsocketError):
    """Action is unsupported on this device."""
