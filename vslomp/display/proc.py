import concurrent.futures as conc
import contextlib
import dataclasses
import enum
import functools
from pathlib import Path
from queue import Queue
from threading import Timer
from typing import Any, BinaryIO, Callable, ClassVar, NamedTuple, Optional, Tuple, Union

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
    screen_size: Tuple[int, int]


Result = Any


class CommandId(enum.Enum):
    INIT_SCREEN = enum.auto()
    INIT_VIDEO = enum.auto()
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
def create(screen_name: str, executor: conc.Executor):
    (
        epd,
        size,
    ) = screen_utils.get_screen(screen_name)
    with screen.ScreenProcessorFactory(
        executor=executor, cxt=epd
    ) as sph, imager.ImagerProcessorFactory(executor=executor, cxt=None) as iph:
        with DisplayProcessorFactory(executor=executor, cxt=Context(sph, iph, size)) as dph:
            yield dph
    logevent("EXIT", "DisplayProcessorContextManager")


_buffer: "Queue[Tuple[Image.Image, Optional[int], disp_utils.Tags]]" = Queue()
last_timer: Optional[Timer] = None


class Cmd:
    @dataclasses.dataclass
    class InitScreen(_DisplayCommand):
        cmdid = CommandId.INIT_SCREEN

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            cxt.screen.send(screen.Cmd.Init(), pri=10).or_err(lambda ex, t: print(ex))

    INIT_SCREEN = InitScreen()

    @dataclasses.dataclass
    class InitVideo(_DisplayCommand):
        cmdid = CommandId.INIT_VIDEO
        firstFrame: ClassVar[bool] = True

        ondisplay: Callable[[int], None]
        wait: Optional[float] = None

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            global _buffer, last_timer

            def _pushnext(res: None, tags: Any, *, frame: Optional[int]):
                _wait = self.wait if self.wait else 0.0
                if Cmd.InitVideo.firstFrame:
                    _wait = 0.0
                    Cmd.InitVideo.firstFrame = False
                last_timer = Timer(_wait, _display)
                last_timer.setName(f"PushNextFrame[{_wait}]")
                last_timer.start()

                if frame:
                    self.ondisplay(frame)

            def _display():
                img, frno, tags = _buffer.get(block=True)
                cxt.screen.send(screen.Cmd.Display(img), tags=tags).then(
                    functools.partial(_pushnext, frame=frno)
                )
                _buffer.task_done()

            _buffer = Queue()
            # sends frames one-by-one to the screen processor so we have a chance to interrupt
            _pushnext(None, None, frame=None)

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
                    imager.Cmd.EnsureSize(img, cxt.screen_size, fill=0, resample=Image.ANTIALIAS),
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
            global _buffer

            def _bufferput(img: Image.Image, tags: disp_utils.Tags):
                _buffer.put((img, self.frame, tags), block=True)

            def _convert(img: Image.Image, tags: disp_utils.Tags):
                cxt.imager.send(
                    imager.Cmd.Convert(img, "1", Image.FLOYDSTEINBERG), tags=tags
                ).then(_bufferput)

            cxt.imager.send(
                imager.Cmd.EnsureSize(self.img, cxt.screen_size, Image.ANTIALIAS),
                tags=[("frame", self.frame)],
            ).then(_convert)

    class Finish(_DisplayCommand):
        cmdid = CommandId.FINISH

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            global _buffer, last_timer

            _last_timer = last_timer
            if _last_timer:
                _last_timer.cancel()

            cxt.imager.join()
            _buffer.join()
            cxt.screen.join()

    FINISH = Finish()

    class Sleep(_DisplayCommand):
        cmdid = CommandId.SLEEP

        def exec(self, hcmd: DisplayCommandHandle, cxt: Context) -> Result:
            cxt.screen.join()
            cxt.screen.send(screen.Cmd.Clear(), 100)
            cxt.screen.send(screen.Cmd.Sleep(), 101)
            cxt.screen.send(screen.Cmd.Uninit(), 102)
            cxt.screen.join()

    SLEEP = Sleep()
