from typing import Optional

from PIL import Image
from waveshare_epd import epd7in5_V2 as epd  # type:ignore

DataType = Optional[Image.Image]

def cmd_init(epd: epd.EPD, data: DataType) -> None:
    epd.init()


def cmd_clear(epd: epd.EPD, data: DataType) -> None:
    epd.Clear()


def cmd_sleep(epd: epd.EPD, data: DataType) -> None:
    epd.sleep()


def cmd_display(epd: epd.EPD, data: DataType) -> None:
    if isinstance(data, Image.Image):
        epd.display(epd.getbuffer(data))  # type:ignore

def cmd_uninit(epd: epd.EPD, data: DataType) -> None:
    epd.Dev_exit()
