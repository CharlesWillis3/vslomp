import asyncio
from typing import Any, Optional

from PIL.Image import FLOYDSTEINBERG, Image

import vslomp.display.imager.cmds as imager
import vslomp.display.imager.proc as imager_proc
import vslomp.display.screen.cmds as screen
import vslomp.display.screen.proc as screen_proc
from cmdq.cmdproc import CmdHandle


def main():
    print("Running VsloMP")
    scp = screen_proc.CmdProc()
    icp = imager_proc.CmdProc()

    def error_handler(hcmd: CmdHandle[Any], ex: Exception):
        print("ERROR", hcmd, str(ex.args))

    def icp_handler(hcmd: CmdHandle[imager.ImagerCmd], img: Optional[Any]):
        if isinstance(img, Image):
            if hcmd.tcmd == imager.LoadFile:
                cmd = imager.EnsureSize(img, (800, 480), 0)
                icp.send(cmd)
            elif hcmd.tcmd == imager.EnsureSize:
                cmd = imager.Convert(img, "1", FLOYDSTEINBERG)
                icp.send(cmd)
            else:
                scp.send(screen.Display(img))
        else:
            raise ValueError(type(img))

    def scp_handler(hcmd: CmdHandle[screen.ScreenCmd], res: Optional[Any]):
        if hcmd.tcmd == screen.Display:
            scp.send(screen.Wait(10))
            scp.send(screen.Clear, pri=100)
            scp.send(screen.Sleep, pri=200)
            scp.send(screen.Uninit, pri=250)

    scp.on_error(error_handler).on_result(scp_handler)
    icp.on_error(error_handler).on_result(icp_handler)

    scp.start()
    icp.start()

    scp.send(screen.Init)
    scp.send(screen.Clear)
    icp.send(imager.LoadFile("/home/pi/images/001.jpg"))

    icp.join()
    scp.join()

    del(icp)
    del(scp)

    return None

main()