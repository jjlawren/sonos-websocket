"""Tests for SonosWebsocket."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sonos_websocket import SonosWebsocket

PLAYER_ID = "RINCON_1234567890"
CLIP_ID_VALUE = "clip-abc-123"
TEST_URI = "http://example.com/clip.mp3"


@pytest.fixture
def ws() -> SonosWebsocket:
    """Return a SonosWebsocket instance with a pre-set player ID."""
    mock_session = MagicMock()
    mock_session.closed = False
    instance = SonosWebsocket(
        "192.168.1.100", player_id=PLAYER_ID, session=mock_session
    )
    return instance


async def test_play_clip(ws: SonosWebsocket) -> None:
    """play_clip sends loadAudioClip with the expected namespace and streamUrl."""
    expected_response = [{"success": True}, {"id": CLIP_ID_VALUE, "status": "ACTIVE"}]

    with patch.object(
        ws, "send_command", new=AsyncMock(return_value=expected_response)
    ) as mock_send:
        result = await ws.play_clip(TEST_URI)

    command, options = mock_send.call_args.args
    assert command["namespace"] == "audioClip:1"
    assert command["command"] == "loadAudioClip"
    assert command["playerId"] == PLAYER_ID
    assert options["streamUrl"] == TEST_URI
    assert "volume" not in options
    assert result == expected_response


async def test_play_clip_with_volume(ws: SonosWebsocket) -> None:
    """play_clip includes volume in options when provided."""
    with patch.object(
        ws, "send_command", new=AsyncMock(return_value=[{}, {}])
    ) as mock_send:
        await ws.play_clip(TEST_URI, volume=50)

    _, options = mock_send.call_args.args
    assert options["volume"] == 50


async def test_cancel_clip(ws: SonosWebsocket) -> None:
    """cancel_clip sends cancelAudioClip with the clip ID in options."""
    expected_response = [{"success": True}, {}]

    with patch.object(
        ws, "send_command", new=AsyncMock(return_value=expected_response)
    ) as mock_send:
        result = await ws.cancel_clip(CLIP_ID_VALUE)

    command, options = mock_send.call_args.args
    assert command["namespace"] == "audioClip:1"
    assert command["command"] == "cancelAudioClip"
    assert command["playerId"] == PLAYER_ID
    assert options["id"] == CLIP_ID_VALUE
    assert result == expected_response
