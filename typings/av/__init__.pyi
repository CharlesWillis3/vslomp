from contextlib import contextmanager
from typing import BinaryIO, Collection, ContextManager, Iterable, Iterator, Literal, Sequence, Union

from PIL.Image import Image

class VideoStream:
    class Codec_Context:
        skip_frame: str

    codec_context: Codec_Context
    frames: int

class VideoFrame:
    def to_image(self) -> Image:
        pass

class StreamContainer:
    video: Sequence[VideoStream]

class InputContainer:
    streams: StreamContainer

    def decode(self, stream: VideoStream) -> Iterable[VideoFrame]:
        pass

@contextmanager
def open(file: Union[str, BinaryIO], mode: Literal["w", "r"] = "r", **kwargs: str) -> Iterator[InputContainer]:
        pass
