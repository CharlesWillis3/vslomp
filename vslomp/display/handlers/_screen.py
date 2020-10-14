from waveshare_epd import epd7in5_V2 as epd # type:ignore
from cmdq.cmdq.cmdproc import UnknownCmdError

def raise_unknown(epd: epd.EPD, data: None = None) -> None:
    raise UnknownCmdError

def cmd_init(epd: epd.EPD, data: None = None) -> None:
    epd.init()


def cmd_clear(epd: epd.EPD, data: None = None) -> None:
    epd.Clear()


def cmd_sleep(epd: epd.EPD, data: None = None) -> None:
    epd.sleep()