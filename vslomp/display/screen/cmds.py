import time
from abc import ABC, abstractmethod

from PIL.Image import Image
from waveshare_epd.epd7in5_V2 import EPD  # type:ignore

from cmdq.exceptions import UnknownCmdError


class ScreenCmd(ABC):
    @abstractmethod
    def __call__(self, epd: EPD) -> None:
        raise UnknownCmdError


class Wait(ScreenCmd):
    def __init__(self, secs: float) -> None:
        self.secs = secs

    def __call__(self, epd: EPD) -> None:
        time.sleep(self.secs)


class Init(ScreenCmd):
    def __call__(self, epd: EPD) -> None:
        epd.init()


class Clear(ScreenCmd):
    def __call__(self, epd: EPD) -> None:
        epd.Clear()


class Sleep(ScreenCmd):
    def __call__(self, epd: EPD) -> None:
        epd.sleep()


class Uninit(ScreenCmd):
    def __call__(self, epd: EPD) -> None:
        epd.Dev_exit()


class Display(ScreenCmd):
    def __init__(self, img: Image) -> None:
        self.img = img

    def __call__(self, epd: EPD) -> None:
        epd.display(epd.getbuffer(self.img))  # type:ignore


class Terminate(ScreenCmd):
    def __call__(self, epd: EPD) -> None:
        pass
