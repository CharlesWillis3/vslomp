import concurrent.futures as conc
import contextlib
import dataclasses
import enum
from pathlib import Path
from queue import Queue
from threading import Timer
from typing import Any, BinaryIO, ClassVar, NamedTuple, Optional, Tuple, Union

import PIL.Image as Image
import qcmd.core as qcore
import qcmd.processors.executor as q
from qcmd.core import logevent

import vslomp.display.imager.proc as imager
import vslomp.display.screen.proc as screen
import vslomp.display.screen.utils as screen_utils
import vslomp.display.utils as disp_utils
from vslomp.display.screen.utils import EPDMonochromeProtocol


class Context(NamedTuple):
    screen: qcore.CommandProcessor[screen.CommandId, EPDMonochromeProtocol]
    imager: qcore.CommandProcessor[imager.CommandId, None]


Result = Any


class CommandId(enum.Enum):
    INIT = enum.auto()
    CLEAR = enum.auto()
    SPLASHSCREEN = enum.auto()
    DISPLAY = enum.auto()
    FINISH = enum.auto()
    SLEEP = enum.auto()


class DisplayProcessorFactory(q.ProcessorFactory[CommandId, Context]):
    procname = "Display"


DisplayProcessor = q.Processor[CommandId, Context]
DisplayCommandHandle = q.CommandHandle[CommandId, None]
_DisplayCommand = q.Command[CommandId, Context, None]


@contextlib.contextmanager
def create(executor: conc.Executor):
    with screen.ScreenProcessorFactory(
        executor=executor, cxt=screen_utils.Screen
    ) as sph, imager.ImagerProcessorFactory(executor=executor, cxt=None) as iph:
        with DisplayProcessorFactory(executor=executor, cxt=Context(sph, iph)) as dph:
            yield dph
    logevent("EXIT", "DisplayProcessorContextManager")


_buffer: "Queue[Tuple[Image.Image, disp_utils.Tags]]" = Queue()
last_timer: Optional[Timer] = None


class Cmd:
    @dataclasses.dataclass
    class Init(_DisplayCommand):
        cmdid = CommandId.INIT
        firstFrame: ClassVar[bool] = True

        wait: Optional[float] = None

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            def _pushnext(res: None, tags: Any):
                _wait = self.wait if self.wait else 0.0
                if Cmd.Init.firstFrame:
                    _wait = 0.0
                    Cmd.Init.firstFrame = False
                timer = Timer(_wait, _display)
                timer.setName("PushNextFrame")
                timer.start()

            def _display():
                img, tags = _buffer.get(block=True)
                cxt.screen.send(screen.Cmd.Display(img), tags=tags).then(_pushnext)
                _buffer.task_done()

            cxt.screen.send(screen.Cmd.Init(), pri=10)

            # sends frames one-by-one to the screen processor so we have a chance to interrupt
            _pushnext(None, None)

    class Clear(_DisplayCommand):
        cmdid = CommandId.CLEAR

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            cxt.screen.send(screen.Cmd.Clear())

    CLEAR = Clear()

    @dataclasses.dataclass
    class Splashscreen(_DisplayCommand):
        cmdid = CommandId.SPLASHSCREEN

        resource: Union[str, Path, BinaryIO]

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            def _display(img: Image.Image, tags: Any):
                cxt.screen.send(screen.Cmd.Display(img), pri=45, tags=tags)

            def _convert(img: Image.Image, tags: Any):
                cxt.imager.send(
                    imager.Cmd.Convert(img, mode="1", dither=Image.FLOYDSTEINBERG),
                    tags=tags,
                    pri=45,
                ).then(_display)

            def _size(img: Image.Image, tags: Any):
                cxt.imager.send(
                    imager.Cmd.EnsureSize(
                        img, screen_utils.screen_size, fill=0, resample=Image.ANTIALIAS
                    ),
                    pri=45,
                    tags=tags,
                ).then(_convert)

            cxt.imager.send(
                imager.Cmd.LoadFile(self.resource), tags=[("splashscreen", 0)], pri=45
            ).then(_size)

    @dataclasses.dataclass
    class Display(_DisplayCommand):
        cmdid = CommandId.DISPLAY

        img: Image.Image
        frame: Optional[int]

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            def _bufferput(img: Image.Image, tags: disp_utils.Tags):
                _buffer.put((img, tags), block=True)

            def _convert(img: Image.Image, tags: disp_utils.Tags):
                cxt.imager.send(
                    imager.Cmd.Convert(img, "1", Image.FLOYDSTEINBERG), tags=tags
                ).then(_bufferput)

            cxt.imager.send(
                imager.Cmd.EnsureSize(self.img, screen_utils.screen_size, Image.ANTIALIAS),
                tags=[("frame", self.frame)],
            ).then(_convert)

    class Finish(_DisplayCommand):
        cmdid = CommandId.FINISH

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            cxt.imager.join()
            cxt.imager.halt()
            _buffer.join()

    FINISH = Finish()

    class Sleep(_DisplayCommand):
        cmdid = CommandId.SLEEP

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            global last_timer
            cxt.screen.join()
            cxt.screen.send(screen.Cmd.Clear(), 100)
            cxt.screen.send(screen.Cmd.Sleep(), 101)
            cxt.screen.send(screen.Cmd.Uninit(), 102)
            cxt.screen.join()

            _last_timer = last_timer
            if _last_timer:
                _last_timer.cancel()

    SLEEP = Sleep()
