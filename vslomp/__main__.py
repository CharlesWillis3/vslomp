import logging
from typing import Any, Container

from PIL import Image

import vslomp.display.proc as display
import vslomp.video.proc as video
from vslomp.display.proc import Cmd as dcmd
from vslomp.video.proc import Cmd as vcmd


def main():
    print("very SLO movie player")
    logging.basicConfig(level=logging.INFO)

    with video.VideoProcessorHandle(None) as vph, display.create() as dph:

        def _onimage(img: Image.Image, frame: int, tags: Container[Any]) -> None:
            dph.send(dcmd.Display(img, frame), tags=[("frame", frame)])

        def _generate(res: video.LoadResult, tags: Container[Any]) -> None:
            print("HEY!!", res.frames)
            vph.send(vcmd.GenerateImages(res, _onimage, start=10, step=5))
            vph.send(vcmd.Unload())

        dph.send(dcmd.Init(wait=60 * 5))
        dph.send(dcmd.Clear(), pri=45)

        dph.send(dcmd.Splashscreen(("/home/pi/images/001.jpg")), pri=46)

        vph.send(
            vcmd.Load(
                "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov",
                video_stream=0,
                skip_frame="NONKEY",
            )
        ).then(_generate)

        vph.join()
        vph.halt()
        dph.join()
        dph.send(dcmd.Finish())
        dph.send(dcmd.Sleep())
        dph.join()

    return None


if __name__ == "__main__":
    main()
