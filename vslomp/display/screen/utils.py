import importlib
from typing import Protocol, Sequence, cast

from PIL import Image


class EPDMonochromeProtocol(Protocol):
    def __init__(self) -> None:
        raise NotImplementedError

    def init(self) -> None:
        raise NotImplementedError

    def getbuffer(self, image: Image.Image) -> Sequence[int]:
        raise NotImplementedError

    def display(self, image: Sequence[int]) -> None:
        raise NotImplementedError

    def Clear(self) -> None:
        raise NotImplementedError

    def sleep(self) -> None:
        raise NotImplementedError

    def Dev_exit(self) -> None:
        raise NotImplementedError


epd_module = importlib.import_module("waveshare_epd." + "epd7in5_V2")
_EPD = getattr(epd_module, "EPD")
Screen = cast(EPDMonochromeProtocol, _EPD())
screen_size = (getattr(epd_module, "EPD_WIDTH"), getattr(epd_module, "EPD_HEIGHT"))
