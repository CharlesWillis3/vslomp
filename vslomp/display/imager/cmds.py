from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from PIL import Image

from cmdq.exceptions import UnknownCmdError


class ImagerCmd(ABC):
    @abstractmethod
    def __call__(self) -> Any:
        raise UnknownCmdError


class LoadFile(ImagerCmd):
    def __init__(self, path: str) -> None:
        self.path = path

    def __call__(self) -> Image.Image:
        return Image.open(self.path)


class Convert(ImagerCmd):
    def __init__(
        self, img: Image.Image, mode: Optional[str], dither: int = Image.FLOYDSTEINBERG
    ) -> None:
        self.img = img
        self.mode = mode
        self.dither = dither

    def __call__(self) -> Image.Image:
        return self.img.convert(mode=self.mode, dither=self.dither)  # type:ignore


class EnsureSize(ImagerCmd):
    def __init__(self, img: Image.Image, size: Tuple[int, int], fill: int = 0) -> None:
        self.img = img
        self.size = size
        self.fill = fill

    def __call__(self) -> Image.Image:
        img = self.img
        img.thumbnail(self.size, resample=Image.ANTIALIAS)

        img_w, img_h = img.size
        des_w, des_h = self.size
        if img_w < des_w or img_h < des_h:
            bg = Image.new(img.mode, self.size, 0)  # type:ignore
            box_tlw = (des_w - img_w) // 2
            box_tlh = (des_h - img_h) // 2
            bg.paste(img, (max(0, box_tlw), max(0, box_tlh)))
            return bg
        else:
            return img
