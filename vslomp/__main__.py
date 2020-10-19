import itertools
import logging
from operator import contains
from typing import Any, Optional

import av
import av.datasets
from PIL.Image import FLOYDSTEINBERG, Image
from cmdq.base import CommandHandle

import vslomp.display.imager.cmds as imager
import vslomp.display.imager.proc as imager_proc
from cmdq.cmdproc import CmdHandle  # type:ignore
import vslomp.display.screen.tpproc as screen

from waveshare_epd.epd7in5_V2 import EPD

def main():
    print("very SLO movie player")
    logging.basicConfig(level=logging.INFO)

    with screen.ScreenProcessorHandle(EPD()) as scp, imager_proc.CmdProc() as icp:

        def scp_handler(hcmd: CommandHandle[screen.ScreenCommand], res: None):
            if contains(hcmd.tags, "wait"):
                scp.send(screen.WaitCmd(1))

        def icp_handler(hcmd: CmdHandle[imager.ImagerCmd], img: Optional[Any]):
            if isinstance(img, Image):
                if contains(hcmd.tags, "ensure_size"):
                    cmd = imager.EnsureSize(img, (800, 480), 0)
                    icp.send(cmd, tags=["convert"])
                elif contains(hcmd.tags, "convert"):
                    cmd = imager.Convert(img, "1", FLOYDSTEINBERG)
                    icp.send(cmd)
                else:
                    c = screen.DisplayCmd(img)
                    c.onresult = scp_handler
                    scp.send(c, tags=["wait"])
            else:
                raise ValueError(type(img))

        icp.on_result(icp_handler)

        icp.start()

        scp.send(screen.InitCmd())
        scp.send(screen.ClearCmd())
        # icp.send(imager.LoadFile("/home/pi/images/001.jpg"), tags=["ensure_size"])

        with av.open(
            "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov"
        ) as container:
            stream = container.streams.video[0]
            stream.codec_context.skip_frame = "NONKEY"

            for x, frame in enumerate(itertools.islice(container.decode(stream), 0, None)):
                if not x % 10 == 0:
                    continue

                print(x, frame)
                icp.send(imager.EnsureSize(frame.to_image(), (800, 480), 0), tags=["convert"])

        scp.send(screen.ClearCmd(), 100)
        scp.send(screen.SleepCmd(), 100)
        scp.send(screen.UninitCmd(), 100)
        icp.join()
        scp.join()

    return None


main()
