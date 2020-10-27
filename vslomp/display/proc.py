import dataclasses
import enum
from contextlib import contextmanager
from typing import Any, Iterator, NamedTuple, Optional

import cmdq.base as qbase
import cmdq.processors.threadpool as qtp
import PIL.Image as Image
from cmdq.base import logevent

import vslomp.display.imager.tpproc as imager
import vslomp.display.screen.tpproc as screen
import vslomp.display.screen.utils as screen_utils
import vslomp.display.utils as disp_utils


class Context(NamedTuple):
    screen: screen.ScreenProcessor
    imager: imager.ImageProcessor


Result = Any


class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    DISPLAY = enum.auto()
    FINISH = enum.auto()
    SLEEP = enum.auto()


DisplayProcessor = qbase.CommandProcessor[CommandId, Context]
_DisplayProcessor = qtp.Processor[CommandId, Context]


class DisplayProcessorHandle(qtp.ProcessorHandle[CommandId, Context]):
    @classmethod
    def factory(cls, cxt: Context) -> qbase.CommandProcessor[CommandId, Context]:
        return _DisplayProcessor("Display", cxt)


@contextmanager
def create() -> Iterator[DisplayProcessor]:
    with screen.ScreenProcessorHandle(screen_utils.Screen()) as sph, imager.ImagerProcessorHandle(
        None
    ) as iph:
        with DisplayProcessorHandle(Context(sph, iph)) as dph:
            yield dph
    logevent("EXIT", "DisplayProcessorHandle")


_DisplayCommand = qbase.Command[CommandId, Context, Result]


class Cmd:
    class Init(_DisplayCommand):
        cmdId = CommandId.INIT

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.screen.send(screen.InitCmd())

    class Clear(_DisplayCommand):
        cmdId = CommandId.CLEAR

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.screen.send(screen.ClearCmd())

    @dataclasses.dataclass
    class Display(_DisplayCommand):
        cmdId = CommandId.DISPLAY

        img: Image.Image
        frame: Optional[int]
        wait: Optional[float]

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            def _display(img: Image.Image, tags: disp_utils.Tags):
                cxt.screen.send(screen.DisplayCmd(img), tags=tags)
                if self.wait:
                    cxt.screen.send(screen.WaitCmd(self.wait))

            def _convert(img: Image.Image, tags: disp_utils.Tags):
                cxt.imager.send(imager.ConvertCmd(img, "1", Image.FLOYDSTEINBERG)).then(_display)

            cxt.imager.send(
                imager.EnsureSizeCmd(self.img, screen_utils.screen_size, Image.ANTIALIAS),
                tags=[("frame", self.frame)],
            ).then(_convert)

    class Finish(_DisplayCommand):
        cmdId = CommandId.FINISH

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.imager.join()
            cxt.screen.join()

    class Sleep(_DisplayCommand):
        cmdId = CommandId.SLEEP

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.screen.send(screen.ClearCmd(), 100)
            cxt.screen.send(screen.SleepCmd(), 101)
            cxt.screen.send(screen.UninitCmd(), 102)

            cxt.screen.join()
