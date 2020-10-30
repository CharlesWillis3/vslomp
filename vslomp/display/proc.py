import dataclasses
import enum
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import contextmanager
from queue import Queue
from threading import Timer
from typing import Any, Iterator, NamedTuple, Optional, Tuple

import cmdq.base as qbase
import cmdq.processors.threadpool as qtp
import PIL.Image as Image
from cmdq.base import logevent

import vslomp.display.imager.proc as imager
import vslomp.display.screen.proc as screen
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

_buffer: "Queue[Tuple[Image.Image, disp_utils.Tags]]" = Queue()
_executor = ThreadPoolExecutor(thread_name_prefix="Buffer")
last_push_future: "Optional[Future[None]]" = None


class Cmd:
    @dataclasses.dataclass
    class Init(_DisplayCommand):
        cmdId = CommandId.INIT

        wait: Optional[float] = None

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            def _pushnext():
                _wait = self.wait if self.wait else 0.0
                timer = Timer(_wait, _display)
                timer.setName("PushNext")
                timer.start()

            def _schedule(res: None, tags: Any):
                global last_push_future
                last_push_future = _executor.submit(_pushnext)

            def _display():
                img, tags = _buffer.get(block=True)
                cxt.screen.send(screen.Cmd.Display(img), tags=tags).then(_schedule)
                _buffer.task_done()

            cxt.screen.send(screen.Cmd.Init())
            _schedule(None, None)

    class Clear(_DisplayCommand):
        cmdId = CommandId.CLEAR

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.screen.send(screen.Cmd.Clear())

    @dataclasses.dataclass
    class Display(_DisplayCommand):
        cmdId = CommandId.DISPLAY

        img: Image.Image
        frame: Optional[int]

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
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
        cmdId = CommandId.FINISH

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            cxt.imager.join()
            cxt.imager.halt()
            _buffer.join()

    class Sleep(_DisplayCommand):
        cmdId = CommandId.SLEEP

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: Context) -> Result:
            global last_push_future
            cxt.screen.join()
            cxt.screen.send(screen.Cmd.Clear(), 100)
            cxt.screen.send(screen.Cmd.Sleep(), 101)
            cxt.screen.send(screen.Cmd.Uninit(), 102)
            cxt.screen.join()

            _last_push_future = last_push_future
            if _last_push_future:
                _last_push_future.cancel()
            _executor.shutdown(wait=False)
