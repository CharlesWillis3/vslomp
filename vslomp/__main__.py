import asyncio
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional

from grpclib.server import Server
from grpclib.utils import graceful_exit

import vslomp.display.proc as disp
import vslomp.video.proc as video
from vslomp.display.proc import Cmd as dcmd
from vslomp.server import PlayerService


async def main(
    screen_type: str,
    *,
    host: str,
    port: int,
    threads: int,
    log_level: str,
    asyncio_log_level: Optional[str],
):
    print("A very SLO movie player")

    core_logger = logging.getLogger("qcmd.core")
    core_logger.setLevel(log_level)

    if asyncio_log_level:
        aio_logger = logging.getLogger("asyncio")
        aio_logger.setLevel(asyncio_log_level)

    with ThreadPoolExecutor(threads, thread_name_prefix="Server") as tpe:
        with video.VideoProcessorFactory(tpe, None) as vph, disp.create(screen_type, tpe) as dph:

            dph.send(dcmd.INIT_SCREEN, pri=10).or_err(lambda ex, t: print(ex, ex.__class__))
            dph.send(dcmd.CLEAR, pri=45)

            dph.join()

            player = PlayerService(dph, vph)
            server = Server([player])

            with graceful_exit([server]):
                print("SERVING:", f"""{host}:{port}""")
                await server.start(host=host, port=port)
                await server.wait_closed()

            vph.halt()
            dph.join()
            dph.send(dcmd.SLEEP)
            dph.join()

    return None


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(
        prog="vslomp",
        description="A very SLO movie player server",
        fromfile_prefix_chars="@",
    )

    arg_parser.add_argument(
        "screen_type", help="the type of the e-paper display connected to the server"
    )

    arg_parser.add_argument("-i", "--host", default="0.0.0.0")
    arg_parser.add_argument("-p", "--port", default=50051)
    arg_parser.add_argument(
        "-t", "--threads", help="the number of threads to use for running the display", default=7
    )

    arg_parser.add_argument("-l", "--log-level", default="INFO")
    arg_parser.add_argument("-ad", "--asyncio-debug", default=False)
    arg_parser.add_argument("-al", "--asyncio-log-level", default="WARNING")

    args = arg_parser.parse_args()
    print("Using args: ", args)

    asyncio.run(
        main(
            host=args.host,
            port=args.port,
            screen_type=args.screen_type,
            threads=int(args.threads),
            log_level=args.log_level,
            asyncio_log_level=args.asyncio_log_level if args.asyncio_debug else None,
        ),
        debug=args.asyncio_debug,
    )
