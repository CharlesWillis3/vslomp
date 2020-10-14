from __future__ import annotations

from enum import Enum, auto
from typing import Any, Optional

from waveshare_epd import epd7in5_V2 as epd  # type:ignore

from cmdq.cmdq.cmdproc import CmdProc
from .handlers._screen import cmd_clear, cmd_sleep, cmd_init, raise_unknown


class ScreenCmd(Enum):
    INIT = auto()
    CLEAR = auto()
    SLEEP = auto()


class ScreenCmdProc(CmdProc[ScreenCmd]):
    __handlers = {
        ScreenCmd.INIT: cmd_init,
        ScreenCmd.CLEAR: cmd_clear,
        ScreenCmd.SLEEP: cmd_sleep,
    }

    def __init__(self):
        super().__init__()
        self._epd = epd.EPD()

    async def _handle_msg(self, cmd: ScreenCmd, data: Optional[Any]) -> Optional[Any]:
        return ScreenCmdProc.__handlers.get(cmd, raise_unknown)(self._epd, data)