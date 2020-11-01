import dataclasses
import enum
from time import sleep

import qcmd.processors.executor as q
from PIL.Image import Image

from .utils import EPDMonochromeProtocol


class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    WAIT = enum.auto()
    SLEEP = enum.auto()
    UNINIT = enum.auto()


class ScreenProcessorFactory(q.ProcessorFactory[CommandId, EPDMonochromeProtocol]):
    procname = "Screen"


ScreenProcessor = q.Processor[CommandId, EPDMonochromeProtocol]


_ScreenCommand = q.Command[CommandId, EPDMonochromeProtocol, None]
ScreenCommandHandle = q.CommandHandle[CommandId, None]


class Cmd:
    class Init(_ScreenCommand):
        cmdid = CommandId.INIT

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            cxt.init()

    INIT = Init()

    class Clear(_ScreenCommand):
        cmdid = CommandId.CLEAR

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            cxt.Clear()

    CLEAR = Clear()

    @dataclasses.dataclass
    class Display(_ScreenCommand):
        cmdid = CommandId.DISPLAY
        img: Image

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            cxt.display(cxt.getbuffer(self.img))

    @dataclasses.dataclass
    class Wait(_ScreenCommand):
        cmdid = CommandId.WAIT
        wait: float

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            sleep(self.wait)

    class Sleep(_ScreenCommand):
        cmdid = CommandId.SLEEP

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            cxt.sleep()

    SLEEP = Sleep()

    class Uninit(_ScreenCommand):
        cmdid = CommandId.UNINIT

        def exec(self, hcmd: ScreenCommandHandle, cxt: EPDMonochromeProtocol) -> None:
            cxt.Dev_exit()

    UNINIT = Uninit()
