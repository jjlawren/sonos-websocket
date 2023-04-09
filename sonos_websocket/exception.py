"""Exceptions used by sonos_websocket."""


class SonosWebsocketError(Exception):
    """Base exception for Sonos websockets."""


class Unauthorized(SonosWebsocketError):
    """Authorization rejected when connecting to a Sonos websocket."""


class SonosWSConnectionError(SonosWebsocketError):
    """Connection error encountered on a Sonos websocket."""
