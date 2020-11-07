import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any, Container

from grpclib.server import Server
from PIL import Image

import vslomp.display.proc as display
import vslomp.video.proc as video
from vslomp.display.proc import Cmd as dcmd
from vslomp.server import PlayerService
from vslomp.video.proc import Cmd as vcmd


def main():
    print("very SLO movie player")
    logging.basicConfig(level=logging.INFO)

    with ThreadPoolExecutor(5, thread_name_prefix="Server") as tpe:
        with video.VideoProcessorFactory(tpe, None) as vph, display.create(
            "epd7in5_V2", tpe
        ) as dph:

            def _onimage(img: Image.Image, frame: int, tags: Container[Any]) -> None:
                dph.send(dcmd.Display(img, frame), tags=[("frame", frame)])

            def _generate(res: video.LoadResult, tags: Container[Any]) -> None:
                print("HEY!!", res.frames)
                vph.send(vcmd.GenerateImages(res, _onimage, start=80, step=10))
                vph.send(vcmd.Unload())

            dph.send(dcmd.Init(wait=2))
            dph.send(dcmd.CLEAR, pri=45)

            player = PlayerService()

            server = Server([player])
            server.start(path="")
            server.serve_forever()

            dph.send(dcmd.Splashscreen(("/home/pi/images/001.jpg")), pri=46)

            vph.send(
                vcmd.Load(
                    "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov",
                    vstream_idx=0,
                    skip_frame="NONKEY",
                )
            ).then(_generate)

            vph.join()
            vph.halt()
            dph.join()
            dph.send(dcmd.FINISH)
            dph.send(dcmd.SLEEP)
            dph.join()

    return None


if __name__ == "__main__":
    main()
