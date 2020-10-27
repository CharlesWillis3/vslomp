import dataclasses
import enum
import itertools
from typing import Any, Callable, Container, Optional

import av
import cmdq.base as qbase
import cmdq.processors.threadpool as qtp
from PIL import Image

Result = Any


class CommandId(enum.Enum):
    GENERATE_IMAGES = enum.auto()


VideoProcessor = qbase.CommandProcessor[CommandId, None]
_VideoProcessor = qtp.Processor[CommandId, None]


class VideoProcessorHandle(qtp.ProcessorHandle[CommandId, None]):
    @classmethod
    def factory(cls, cxt: None = None) -> qbase.CommandProcessor[CommandId, None]:
        return _VideoProcessor("Video", cxt)


_VideoCommand = qbase.Command[CommandId, None, Result]


class Cmd:
    @dataclasses.dataclass
    class GenerateImages(_VideoCommand):
        cmdId = CommandId.GENERATE_IMAGES

        resource: str
        onimage: Callable[[Image.Image, int, Container[Any]], None]
        video_stream: int
        skip_frame: Optional[str] = None
        start: Optional[int] = 0
        stop: Optional[int] = None
        step: Optional[int] = None

        def exec(self, hcmd: qbase.CommandHandle[CommandId, Result], cxt: None) -> Result:
            with av.open(self.resource) as container:
                stream = container.streams.video[self.video_stream]
                if self.skip_frame:
                    stream.codec_context.skip_frame = self.skip_frame

                for x, vframe in enumerate(
                    itertools.islice(container.decode(stream), self.start, self.stop, self.step)
                ):
                    self.onimage(vframe.to_image(), x, hcmd.tags)
