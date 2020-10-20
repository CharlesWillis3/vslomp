import enum
from dataclasses import dataclass
from time import sleep

from cmdq.base import Command, CommandHandle, CommandProcessor
from cmdq.processors.threadpool import CmdProcessor, ProcHandle
from PIL.Image import Image
from waveshare_epd.epd7in5_V2 import EPD


class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    WAIT = enum.auto()
    SLEEP = enum.auto()
    UNINIT = enum.auto()


ScreenProcessor = CmdProcessor[CommandId, EPD]


class ScreenProcHandle(ProcHandle[CommandId, EPD]):
    @classmethod
    def factory(cls, cxt: EPD) -> CommandProcessor[CommandId, EPD]:
        return ScreenProcessor("Screen", cxt)


_ScreenCommand = Command[CommandId, EPD, None]


class InitCmd(_ScreenCommand):
    cmdId = CommandId.INIT

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        cxt.init()


class ClearCmd(_ScreenCommand):
    cmdId = CommandId.CLEAR

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        cxt.Clear()


@dataclass
class DisplayCmd(_ScreenCommand):
    cmdId = CommandId.DISPLAY
    img: Image

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        cxt.display(cxt.getbuffer(self.img))


@dataclass
class WaitCmd(_ScreenCommand):
    cmdId = CommandId.WAIT
    wait: float

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        sleep(self.wait)


class SleepCmd(_ScreenCommand):
    cmdId = CommandId.SLEEP

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        cxt.sleep()


class UninitCmd(_ScreenCommand):
    cmdId = CommandId.UNINIT

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: EPD) -> None:
        cxt.Dev_exit()
