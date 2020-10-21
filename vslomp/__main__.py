import itertools
import logging
from typing import Any, Container

import av
import av.datasets
from PIL.Image import FLOYDSTEINBERG, Image
from waveshare_epd.epd7in5_V2 import EPD

import vslomp.display.imager.tpproc as imager
import vslomp.display.screen.tpproc as screen


def main():
    print("very SLO movie player")
    logging.basicConfig(level=logging.INFO)

    with screen.ScreenProcHandle(EPD()) as scp, imager.ImagerProcHandle(None) as icp:

        def _display(img: Image, tags: Container[Any]) -> None:
            scp.send(screen.DisplayCmd(img), tags=tags)
            scp.send(screen.WaitCmd(1.25))

        icp.start()

        scp.send(screen.InitCmd())
        scp.send(screen.ClearCmd())
        # icp.send(imager.LoadFile("/home/pi/images/001.jpg"), tags=["ensure_size"])

        with av.open(
            "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov"
        ) as container:
            stream = container.streams.video[0]
            stream.codec_context.skip_frame = "NONKEY"

            for x, frame in enumerate(itertools.islice(container.decode(stream), 100, None)):
                if not x % 10 == 0:
                    continue

                print(x, frame)
                cmd = imager.EnsureSizeCmd(frame.to_image(), (800, 480), 0)
                icp.send(cmd, tags=[("frame", x)]).then(
                    lambda res, tags: icp.send(
                        imager.ConvertCmd(res, "1", FLOYDSTEINBERG), tags=tags
                    ).then(_display)
                )

        icp.join()
        scp.join()

        scp.send(screen.ClearCmd(), 100)
        scp.send(screen.SleepCmd(), 100)
        scp.send(screen.UninitCmd(), 100)

    return None


if __name__ == "__main__":
    main()
