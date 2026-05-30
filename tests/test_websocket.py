"""Tests for SonosWebsocket."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sonos_websocket import CLIP_ID, SonosWebsocket

PLAYER_ID = "RINCON_1234567890"
CLIP_ID_VALUE = "clip-abc-123"
TEST_URI = "http://example.com/clip.mp3"


@pytest.fixture
def ws():
    """Return a SonosWebsocket instance with a pre-set player ID."""
    mock_session = MagicMock()
    mock_session.closed = False
    instance = SonosWebsocket("192.168.1.100", player_id=PLAYER_ID, session=mock_session)
    return instance


@pytest.mark.asyncio
async def test_play_clip_sends_correct_command(ws):
    """play_clip sends loadAudioClip with the expected namespace and streamUrl."""
    expected_response = [{"success": True}, {CLIP_ID: CLIP_ID_VALUE, "status": "ACTIVE"}]

    with patch.object(ws, "send_command", new=AsyncMock(return_value=expected_response)) as mock_send:
        result = await ws.play_clip(TEST_URI)

    command, options = mock_send.call_args.args
    assert command["namespace"] == "audioClip:1"
    assert command["command"] == "loadAudioClip"
    assert command["playerId"] == PLAYER_ID
    assert options["streamUrl"] == TEST_URI
    assert result == expected_response


@pytest.mark.asyncio
async def test_play_clip_with_volume(ws):
    """play_clip includes volume in options when provided."""
    with patch.object(ws, "send_command", new=AsyncMock(return_value=[{}, {}])) as mock_send:
        await ws.play_clip(TEST_URI, volume=50)

    _, options = mock_send.call_args.args
    assert options["volume"] == 50


@pytest.mark.asyncio
async def test_play_clip_without_volume_omits_key(ws):
    """play_clip does not include volume in options when not provided."""
    with patch.object(ws, "send_command", new=AsyncMock(return_value=[{}, {}])) as mock_send:
        await ws.play_clip(TEST_URI)

    _, options = mock_send.call_args.args
    assert "volume" not in options


@pytest.mark.asyncio
async def test_cancel_clip_sends_correct_command(ws):
    """cancel_clip sends cancelAudioClip with the clip ID in options."""
    expected_response = [{"success": True}, {}]

    with patch.object(ws, "send_command", new=AsyncMock(return_value=expected_response)) as mock_send:
        result = await ws.cancel_clip(CLIP_ID_VALUE)

    command, options = mock_send.call_args.args
    assert command["namespace"] == "audioClip:1"
    assert command["command"] == "cancelAudioClip"
    assert command["playerId"] == PLAYER_ID
    assert options[CLIP_ID] == CLIP_ID_VALUE
    assert result == expected_response


@pytest.mark.asyncio
async def test_cancel_clip_uses_clip_id_constant(ws):
    """The options key for the clip ID matches the exported CLIP_ID constant."""
    with patch.object(ws, "send_command", new=AsyncMock(return_value=[{}, {}])) as mock_send:
        await ws.cancel_clip(CLIP_ID_VALUE)

    _, options = mock_send.call_args.args
    # CLIP_ID constant must be present as a key in the options dict
    assert CLIP_ID in options
    assert options[CLIP_ID] == CLIP_ID_VALUE


@pytest.mark.asyncio
async def test_play_then_cancel_clip(ws):
    """Clip ID returned by play_clip can be used directly with cancel_clip."""
    play_response = [{"success": True}, {CLIP_ID: CLIP_ID_VALUE, "status": "ACTIVE"}]
    cancel_response = [{"success": True}, {}]

    with patch.object(ws, "send_command", new=AsyncMock(side_effect=[play_response, cancel_response])) as mock_send:
        _, play_data = await ws.play_clip(TEST_URI)
        clip_id = play_data[CLIP_ID]
        await ws.cancel_clip(clip_id)

    assert mock_send.call_count == 2
    cancel_command, cancel_options = mock_send.call_args.args
    assert cancel_command["command"] == "cancelAudioClip"
    assert cancel_options[CLIP_ID] == CLIP_ID_VALUE
