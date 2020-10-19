# type:ignore

import itertools
import logging

import av
import av.datasets
from PIL.Image import FLOYDSTEINBERG, Image

import vslomp.display.screen.tpproc as screen
import vslomp.display.imager.tpproc as imager

from waveshare_epd.epd7in5_V2 import EPD

def main():
    print("very SLO movie player")
    logging.basicConfig(level=logging.INFO)

    with screen.ScreenProcHandle(EPD()) as scp, imager.ImagerProcHandle(None) as icp:

        def icp_handler(hcmd: imager.ImagerCommandHandle, img: Image):
            if  hcmd.cmd == imager.CommandId.ENSURE_SIZE:
                cmd = imager.ConvertCmd(img, "1", FLOYDSTEINBERG)
                cmd.onresult = icp_handler
                icp.send(cmd, tags=hcmd.tags)
            else:
                c = screen.DisplayCmd(img)
                scp.send(c, tags=hcmd.tags)
                scp.send(screen.WaitCmd(1))

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
                cmd.onresult = icp_handler
                icp.send(cmd, tags=[("frame", x)])

        icp.join()
        scp.join()

        scp.send(screen.ClearCmd(), 100)
        scp.send(screen.SleepCmd(), 100)
        scp.send(screen.UninitCmd(), 100)

    return None


main()
