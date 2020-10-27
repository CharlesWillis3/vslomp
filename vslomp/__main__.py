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

    # icp.send(imager.LoadFile("/home/pi/images/001.jpg"), tags=["ensure_size"])

    with video.VideoProcessorHandle(None) as vph, display.create() as dph:

        def _onimage(img: Image.Image, frame: int, tags: Container[Any]) -> None:
            dph.send(dcmd.Display(img, frame, 1.25), tags=tags)

        dph.send(dcmd.Init())
        dph.send(dcmd.Clear())

        vph.send(
            vcmd.GenerateImages(
                "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov",
                _onimage,
                video_stream=0,
                skip_frame="NONKEY",
                step=20,
            )
        )

        vph.join()
        dph.join()
        dph.send(dcmd.Finish())
        dph.send(dcmd.Sleep())
        dph.join()

    return None


if __name__ == "__main__":
    main()
