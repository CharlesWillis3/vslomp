import enum
from dataclasses import dataclass
from time import sleep

from cmdq.base import Command, CommandHandle, CommandProcessor
from cmdq.processors.threadpool import Processor, ProcessorHandle
from PIL.Image import Image

from .utils import Screen


class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    WAIT = enum.auto()
    SLEEP = enum.auto()
    UNINIT = enum.auto()


ScreenProcessor = CommandProcessor[CommandId, Screen]
_ScreenProcessor = Processor[CommandId, Screen]


class ScreenProcessorHandle(ProcessorHandle[CommandId, Screen]):
    @classmethod
    def factory(cls, cxt: Screen) -> CommandProcessor[CommandId, Screen]:
        return _ScreenProcessor("Screen", cxt)


_ScreenCommand = Command[CommandId, Screen, None]


class InitCmd(_ScreenCommand):
    cmdId = CommandId.INIT

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        cxt.init()


class ClearCmd(_ScreenCommand):
    cmdId = CommandId.CLEAR

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        cxt.Clear()


@dataclass
class DisplayCmd(_ScreenCommand):
    cmdId = CommandId.DISPLAY
    img: Image

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        cxt.display(cxt.getbuffer(self.img))


@dataclass
class WaitCmd(_ScreenCommand):
    cmdId = CommandId.WAIT
    wait: float

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        sleep(self.wait)


class SleepCmd(_ScreenCommand):
    cmdId = CommandId.SLEEP

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        cxt.sleep()


class UninitCmd(_ScreenCommand):
    cmdId = CommandId.UNINIT

    def exec(self, hcmd: CommandHandle[CommandId, None], cxt: Screen) -> None:
        cxt.Dev_exit()
