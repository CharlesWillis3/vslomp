import dataclasses
import enum
import pathlib
from typing import BinaryIO, Optional, Tuple, Union

import qcmd.processors.executor as q
from PIL import Image


class CommandId(enum.Enum):
    LOAD_FILE = enum.auto()
    CONVERT = enum.auto()
    ENSURE_SIZE = enum.auto()


class ImagerProcessorFactory(q.ProcessorFactory[CommandId, None]):
    procname = "Imager"


ImagerProcessor = q.Processor[CommandId, None]

ImagerCommandHandle = q.CommandHandle[CommandId, Image.Image]
_ImagerCommand = q.Command[CommandId, None, Image.Image]


class Cmd:
    @dataclasses.dataclass
    class LoadFile(_ImagerCommand):
        cmdid = CommandId.LOAD_FILE

        fp: Union[str, pathlib.Path, BinaryIO]

        def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
            return Image.open(self.fp)

    @dataclasses.dataclass
    class Convert(_ImagerCommand):
        cmdid = CommandId.CONVERT

        img: Image.Image
        mode: Optional[str]
        dither: int = Image.FLOYDSTEINBERG

        def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
            return self.img.convert(mode=self.mode, dither=self.dither)  # type:ignore

    @dataclasses.dataclass
    class EnsureSize(_ImagerCommand):
        cmdid = CommandId.ENSURE_SIZE

        img: Image.Image
        size: Tuple[int, int]
        fill: int = 0
        resample: int = Image.ANTIALIAS

        def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
            in_img = self.img
            in_img.thumbnail(self.size, resample=self.resample)

            in_width, in_height = in_img.size
            out_width, out_height = self.size

            if in_width < out_width or in_height < out_height:
                out_img = Image.new(in_img.mode, self.size, 0)  # type:ignore
                place_w = (out_width - in_width) // 2
                place_h = (out_height - in_height) // 2
                out_img.paste(in_img, (max(0, place_w), max(0, place_h)))
                return out_img
            else:
                return in_img
