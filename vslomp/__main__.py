import logging
from operator import contains
from typing import Any, Optional

from PIL.Image import FLOYDSTEINBERG, Image

import vslomp.display.imager.cmds as imager
import vslomp.display.imager.proc as imager_proc
import vslomp.display.screen.cmds as screen
import vslomp.display.screen.proc as screen_proc
from cmdq.cmdproc import CmdHandle  # type:ignore


def main():
    print("vSLOmp")
    logging.basicConfig(level=logging.INFO)

    with screen_proc.CmdProc() as scp, imager_proc.CmdProc() as icp:

        def icp_handler(hcmd: CmdHandle[imager.ImagerCmd], img: Optional[Any]):
            if isinstance(img, Image):
                if contains(hcmd.tags, "ensure_size"):
                    cmd = imager.EnsureSize(img, (800, 480), 0)
                    icp.send(cmd, tags=["convert"])
                elif contains(hcmd.tags, "convert"):
                    cmd = imager.Convert(img, "1", FLOYDSTEINBERG)
                    icp.send(cmd)
                else:
                    scp.send(screen.Display(img))
            else:
                raise ValueError(type(img))

        def scp_handler(hcmd: CmdHandle[screen.ScreenCmd], res: Optional[Any]):
            if hcmd.tcmd == screen.Display:
                scp.send(screen.Wait(1))
                scp.send(screen.Clear, pri=100)
                scp.send(screen.Sleep, pri=200)
                scp.send(screen.Uninit, pri=250)

        scp.on_result(scp_handler)
        icp.on_result(icp_handler)

        scp.start()
        icp.start()

        scp.send(screen.Init)
        scp.send(screen.Clear)
        icp.send(imager.LoadFile("/home/pi/images/001.jpg"), tags=["ensure_size"])

        icp.join()
        scp.join()

    return None


main()
