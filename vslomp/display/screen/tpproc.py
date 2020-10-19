import enum
from time import sleep
from cmdq.base import Command, CommandHandle, CommandProcessor
from waveshare_epd.epd7in5_V2 import EPD
from PIL.Image import Image
from cmdq.processors.threadpool import CmdProcessor, ProcHandle

class ScreenCommand(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    WAIT = enum.auto()
    SLEEP = enum.auto()
    UNINIT = enum.auto()

class _ScreenCommand(Command[ScreenCommand, EPD, None]):
    pass

class InitCmd(_ScreenCommand):
    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.INIT

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        cxt.init()

class ClearCmd(_ScreenCommand):
    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.CLEAR

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        cxt.Clear()

class DisplayCmd(_ScreenCommand):
    def __init__(self, img: Image) -> None:
        self.img = img

    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.DISPLAY

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        cxt.display(cxt.getbuffer(self.img)) # 

class WaitCmd(_ScreenCommand):
    def __init__(self, wait: float) -> None:
        self.wait = wait

    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.WAIT

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        sleep(self.wait)

class SleepCmd(_ScreenCommand):
    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.SLEEP

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        cxt.sleep()

class UninitCmd(_ScreenCommand):
    @property
    def cmd(self) -> ScreenCommand:
        return ScreenCommand.UNINIT

    def exec(self, hcmd: CommandHandle[ScreenCommand], cxt: EPD) -> None:
        cxt.Dev_exit()

class ScreenProcessor(CmdProcessor[ScreenCommand, EPD]):
    pass

class ScreenProcessorHandle(ProcHandle[ScreenCommand, EPD]):
    @classmethod
    def factory(cls, cxt: EPD) -> CommandProcessor[ScreenCommand, EPD]:
        return ScreenProcessor(cxt)