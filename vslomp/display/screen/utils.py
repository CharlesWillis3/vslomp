import importlib
from typing import Protocol, Sequence, Tuple, Type, cast

from PIL import Image


class EPDMonochromeProtocol(Protocol):
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


def get_screen(name: str) -> Tuple[EPDMonochromeProtocol, Tuple[int, int]]:
    epd_module = importlib.import_module("waveshare_epd." + name)
    screen_size = (
        cast(int, getattr(epd_module, "EPD_WIDTH")),
        cast(int, getattr(epd_module, "EPD_HEIGHT")),
    )

    epd_class = cast(Type[EPDMonochromeProtocol], getattr(epd_module, "EPD"))

    return (epd_class(), screen_size)
