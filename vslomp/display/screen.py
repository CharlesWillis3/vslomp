from __future__ import annotations

from enum import Enum, auto
from typing import Any, Callable, Optional

from waveshare_epd import epd7in5_V2 as epd  # type:ignore

from cmdq.cmdproc import CmdProc, UnknownCmdError  # type:ignore

from .handlers._screen import DataType, cmd_clear, cmd_display, cmd_init, cmd_sleep, cmd_uninit


def _raise_unknown(cmd: Any) -> Callable[[epd.EPD, DataType], None]:
    def _inner(_epd: epd.EPD, _data: DataType):
        try:
            raise UnknownCmdError(cmd)
        finally:
            return None

    return _inner


class ScreenCmd(Enum):
    INIT = auto()
    CLEAR = auto()
    SLEEP = auto()
    DISPLAY = auto()
    UNINIT = auto()


class ScreenCmdProc(CmdProc[ScreenCmd]):
    __handlers = {
        ScreenCmd.INIT: cmd_init,
        ScreenCmd.CLEAR: cmd_clear,
        ScreenCmd.SLEEP: cmd_sleep,
        ScreenCmd.DISPLAY: cmd_display,
        ScreenCmd.UNINIT: cmd_uninit,
    }

    def __init__(self):
        super().__init__()
        self._epd = epd.EPD()

    async def _handle_msg(self, cmd: ScreenCmd, data: DataType) -> Optional[Any]:
        return ScreenCmdProc.__handlers.get(cmd, _raise_unknown(cmd))(self._epd, data)