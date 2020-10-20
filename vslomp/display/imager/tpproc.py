import enum
import pathlib
from dataclasses import dataclass
from typing import BinaryIO, Optional, Tuple, Union

from cmdq.base import Command, CommandHandle, CommandProcessor
from cmdq.processors.threadpool import CmdProcessor, ProcHandle
from PIL import Image


class CommandId(enum.Enum):
    LOAD_FILE = enum.auto()
    CONVERT = enum.auto()
    ENSURE_SIZE = enum.auto()


ImagerProcessor = CmdProcessor[CommandId, None]


class ImagerProcHandle(ProcHandle[CommandId, None]):
    @classmethod
    def factory(cls, cxt: None) -> CommandProcessor[CommandId, None]:
        return ImagerProcessor("Imager", cxt)


_ImagerCommand = Command[CommandId, None, Image.Image]


@dataclass
class LoadFileCmd(_ImagerCommand):
    cmdId = CommandId.LOAD_FILE

    fp: Union[str, pathlib.Path, BinaryIO]

    @property
    def cmd(self) -> CommandId:
        return CommandId.LOAD_FILE

    def exec(self, hcmd: CommandHandle[CommandId, Image.Image], cxt: None) -> Image.Image:
        return Image.open(self.fp)


@dataclass
class ConvertCmd(_ImagerCommand):
    cmdId = CommandId.CONVERT

    img: Image.Image
    mode: Optional[str]
    dither: int = Image.FLOYDSTEINBERG

    @property
    def cmd(self) -> CommandId:
        return CommandId.CONVERT

    def exec(self, hcmd: CommandHandle[CommandId, Image.Image], cxt: None) -> Image.Image:
        return self.img.convert(mode=self.mode, dither=self.dither)  # type:ignore


@dataclass
class EnsureSizeCmd(_ImagerCommand):
    cmdId = CommandId.ENSURE_SIZE

    img: Image.Image
    size: Tuple[int, int]
    fill: int = 0
    resample: int = Image.ANTIALIAS

    def exec(self, hcmd: CommandHandle[CommandId, Image.Image], cxt: None) -> Image.Image:
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
