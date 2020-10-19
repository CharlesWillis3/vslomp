from dataclasses import dataclass
import enum
from time import sleep
from cmdq.base import Command, CommandHandle, CommandProcessor
from waveshare_epd.epd7in5_V2 import EPD
from PIL.Image import Image
from cmdq.processors.threadpool import CmdProcessor, ProcHandle

class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    WAIT = enum.auto()
    SLEEP = enum.auto()
    UNINIT = enum.auto()

ScreenCommandHandle = CommandHandle[CommandId]
ScreenProcessor = CmdProcessor[CommandId, EPD]

class ScreenProcHandle(ProcHandle[CommandId, EPD]):
    @classmethod
    def factory(cls, cxt: EPD) -> CommandProcessor[CommandId, EPD]:
        return ScreenProcessor("Screen", cxt)

_ScreenCommand = Command[CommandId, EPD, None]

class InitCmd(_ScreenCommand):
    @property
    def cmd(self) -> CommandId:
        return CommandId.INIT

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        cxt.init()

class ClearCmd(_ScreenCommand):
    @property
    def cmd(self) -> CommandId:
        return CommandId.CLEAR

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        cxt.Clear()

class DisplayCmd(_ScreenCommand):
    def __init__(self, img: Image) -> None:
        self.img = img

    @property
    def cmd(self) -> CommandId:
        return CommandId.DISPLAY

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        cxt.display(cxt.getbuffer(self.img))

@dataclass
class WaitCmd(_ScreenCommand):
    wait: float

    @property
    def cmd(self) -> CommandId:
        return CommandId.WAIT

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        sleep(self.wait)

class SleepCmd(_ScreenCommand):
    @property
    def cmd(self) -> CommandId:
        return CommandId.SLEEP

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        cxt.sleep()

class UninitCmd(_ScreenCommand):
    @property
    def cmd(self) -> CommandId:
        return CommandId.UNINIT

    def exec(self, hcmd: CommandHandle[CommandId], cxt: EPD) -> None:
        cxt.Dev_exit()