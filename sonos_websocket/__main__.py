"""Commandline example to play an audio clip."""
import argparse
import asyncio
import logging

from .websocket import SonosWebsocket

logging.basicConfig(level=logging.DEBUG)


async def main(options):
    """Entrypoint when running as a script."""
    websocket = SonosWebsocket(options.ip_addr)
    await websocket.connect()
    await websocket.play_clip(
        uri=options.uri,
        volume=options.volume,
    )
    await websocket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip_addr", "-i", required=True, help="IP address of Sonos device"
    )
    parser.add_argument(
        "--uri", "-u", required=True, help="URI to audio file to play as clip"
    )
    parser.add_argument(
        "--volume",
        "-V",
        type=int,
        required=False,
        help="Volume level to play at [0-100]",
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
