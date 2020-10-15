import asyncio
from typing import Any, Optional
from PIL.Image import Image, FLOYDSTEINBERG

from cmdq.cmdproc import MsgHandle  # type:ignore

from vslomp.display.screen import ScreenCmd, ScreenCmdProc
from vslomp.display.imager import ImagerCmd, ImagerCmdProc, ImagerCmdData


async def main():

    print("Running vSLOmp")
    scp = ScreenCmdProc()
    icp = ImagerCmdProc()

    def error_handler(hmsg: MsgHandle[Any], ex: Exception):
        print("ERROR", hmsg, str(ex.args))

    async def icp_handler(hmsg: MsgHandle[ImagerCmd], img: Optional[Any]):
        print("DONE",hmsg)
        if isinstance(img, Image):
            if hmsg.cmd == ImagerCmd.LOAD_FILE:
                data = ImagerCmdData.ensure_size(img, (800, 480), 0)
                await icp.send(ImagerCmd.ENSURE_SIZE, data)
            elif hmsg.cmd == ImagerCmd.ENSURE_SIZE:
                data = ImagerCmdData.convert(img, "1", FLOYDSTEINBERG)
                await icp.send(ImagerCmd.CONVERT, data)
            else:
                await scp.send(ScreenCmd.DISPLAY, img)
        else:
            raise ValueError(type(img))

    async def scp_handler(hmsg: MsgHandle[ScreenCmd], res: Optional[Any]):
        print("DONE", hmsg)
        if hmsg.cmd == ScreenCmd.DISPLAY:
            await asyncio.sleep(2)
            await scp.send(ScreenCmd.CLEAR, pri=100)
            await scp.send(ScreenCmd.SLEEP, pri=200)
            await scp.send(ScreenCmd.UNINIT, pri=250)

    await scp.on_error(error_handler)
    await icp.on_error(error_handler)
    await scp.on_result(scp_handler)
    await icp.on_result(icp_handler)

    await scp.start()
    await icp.start()

    await scp.send(ScreenCmd.INIT)
    await scp.send(ScreenCmd.CLEAR)
    await icp.send(ImagerCmd.LOAD_FILE, "/home/pi/images/001.jpg")

    await asyncio.gather(scp.join(), icp.join())


asyncio.run(main())