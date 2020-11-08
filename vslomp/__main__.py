import asyncio
import logging
import os
import tempfile
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Container, Optional

from grpclib.server import Server
from grpclib.utils import graceful_exit
from PIL import Image

import vslomp.display.proc as disp
import vslomp.video.proc as video
from vslomp.display.proc import Cmd as dcmd
from vslomp.server import PlayerService
from vslomp.video.proc import Cmd as vcmd

SOCKET_FILENAME = "vslomp.sock"


async def main(
    screen_type: str, socket_path: Optional[str] = None, threads: int = 5, log_level: str = "INFO"
):
    print("very SLO movie player")
    logging.basicConfig(level=log_level)

    with ThreadPoolExecutor(threads, thread_name_prefix="Server") as tpe:
        with video.VideoProcessorFactory(tpe, None) as vph, disp.create(screen_type, tpe) as dph:

            dph.send(dcmd.INIT_SCREEN, pri=10).or_err(lambda ex, t: print(ex, ex.__class__))
            dph.send(dcmd.CLEAR, pri=45)

            dph.join()

            player = PlayerService(dph, vph)
            server = Server([player])

            if socket_path is None:
                appdata = Path.home() / ".vslomp"
                appdata.mkdir(exist_ok=True)
                socket_file = appdata / SOCKET_FILENAME
                socket_path = str(socket_file)

            with graceful_exit([server]):
                print("SERVING:", socket_path)
                await server.start(path=socket_path)
                await server.wait_closed()

            vph.halt()
            dph.join()
            dph.send(dcmd.FINISH)
            dph.send(dcmd.SLEEP)
            dph.join()

    return None


if __name__ == "__main__":
    asyncio.run(main("epd7in5_V2", socket_path=None, threads=5))
