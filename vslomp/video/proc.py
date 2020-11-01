import dataclasses
import enum
import itertools
from typing import TYPE_CHECKING, Any, Callable, Container, ContextManager, NamedTuple, Optional

import av
import qcmd.processors.executor as q
from PIL import Image

if TYPE_CHECKING:
    from av import InputContainer

Result = Any


class CommandId(enum.Enum):
    LOAD = enum.auto()
    GENERATE_IMAGES = enum.auto()
    UNLOAD = enum.auto()


class VideoProcessorFactory(q.ProcessorFactory[CommandId, None]):
    procname = "Video"


_VideoCommand = q.Command[CommandId, None, Result]
VideoCommandHandle = q.CommandHandle[CommandId, Result]


class LoadResult(NamedTuple):
    container: Any
    stream: Any
    frames: int


_loaded_manager: Optional[ContextManager["InputContainer"]] = None


def _load(resource: str, video_stream: int, skip_frame: Optional[str] = None):
    global _loaded_manager
    frames = 0

    if skip_frame:
        with av.open(resource) as temp_container:
            temp_stream = temp_container.streams.video[video_stream]
            temp_stream.codec_context.skip_frame = skip_frame
            for x, _ in enumerate(temp_container.decode(temp_stream)):
                frames = x

    _loaded_manager = av.open(resource)
    container = _loaded_manager.__enter__()
    stream = container.streams.video[video_stream]
    if skip_frame:
        stream.codec_context.skip_frame = skip_frame

    return LoadResult(container, stream, frames if skip_frame else stream.frames)


class Cmd:
    @dataclasses.dataclass
    class Load(q.Command[CommandId, None, LoadResult]):
        cmdid = CommandId.LOAD

        resource: str
        video_stream: int
        skip_frame: Optional[str] = None

        def exec(self, hcmd: q.CommandHandle[CommandId, LoadResult], cxt: None) -> LoadResult:
            return _load(self.resource, self.video_stream, self.skip_frame)

    @dataclasses.dataclass
    class GenerateImages(_VideoCommand):
        cmdid = CommandId.GENERATE_IMAGES

        loadresult: LoadResult
        onimage: Callable[[Image.Image, int, Container[Any]], None]
        start: Optional[int] = 0
        stop: Optional[int] = None
        step: Optional[int] = None

        def exec(self, hcmd: VideoCommandHandle, cxt: None) -> Result:
            _start = self.start if self.start else 0
            _step = self.step if self.step else 1

            def _calcframe(x: int):
                return _start + (_step * x)

            for x, vframe in enumerate(
                itertools.islice(
                    self.loadresult.container.decode(self.loadresult.stream),
                    self.start,
                    self.stop,
                    self.step,
                )
            ):
                self.onimage(vframe.to_image(), _calcframe(x), hcmd.tags)

    class Unload(_VideoCommand):
        cmdid = CommandId.UNLOAD

        def exec(self, hcmd: VideoCommandHandle, cxt: None) -> Result:
            global _loaded_manager
            if _loaded_manager:
                _loaded_manager.__exit__(None, None, None)
