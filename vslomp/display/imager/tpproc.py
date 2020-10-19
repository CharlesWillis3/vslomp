import enum
import pathlib
from typing import BinaryIO, Optional, Tuple, Union
from dataclasses import dataclass
from PIL import Image

from cmdq.base import Command, CommandHandle, CommandProcessor
from cmdq.processors.threadpool import CmdProcessor, ProcHandle

class CommandId(enum.Enum):
    LOAD_FILE = enum.auto()
    CONVERT = enum.auto()
    ENSURE_SIZE = enum.auto()

ImagerCommandHandle = CommandHandle[CommandId]
ImagerProcessor = CmdProcessor[CommandId, None]

class ImagerProcHandle(ProcHandle[CommandId, None]):
    @classmethod
    def factory(cls, cxt: None) -> CommandProcessor[CommandId, None]:
        return ImagerProcessor("Imager", cxt)

_ImagerCommand = Command[CommandId, None, Image.Image]

@dataclass
class LoadFileCmd(_ImagerCommand):
    fp: Union[str, pathlib.Path, BinaryIO]

    @property
    def cmd(self) -> CommandId:
        return CommandId.LOAD_FILE

    def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
        return Image.open(self.fp)

@dataclass
class ConvertCmd(_ImagerCommand):
    img : Image.Image
    mode : Optional[str]
    dither : int = Image.FLOYDSTEINBERG
    
    @property
    def cmd(self) -> CommandId:
        return CommandId.CONVERT

    def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
        return self.img.convert(mode=self.mode, dither=self.dither) # type:ignore

@dataclass
class EnsureSizeCmd(_ImagerCommand):
    img: Image.Image
    size: Tuple[int, int]
    fill: int = 0
    resample: int = Image.ANTIALIAS

    @property
    def cmd(self) -> CommandId:
        return CommandId.ENSURE_SIZE

    def exec(self, hcmd: ImagerCommandHandle, cxt: None) -> Image.Image:
        i_img = self.img
        i_img.thumbnail(self.size, resample=self.resample)

        i_w, i_h = i_img.size
        o_w, o_h = self.size

        if i_w < o_w or i_h < o_h:
            o_img = Image.new(i_img.mode, self.size, 0) # type:ignore
            place_w = (o_w - i_w) // 2
            place_h = (o_h - i_h) // 2
            o_img.paste(i_img, (max(0, place_w), max(0, place_h)))
            return o_img
        else:
            return i_img
