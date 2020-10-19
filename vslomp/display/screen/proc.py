from __future__ import annotations

from waveshare_epd import epd7in5_V2 as epd  # type:ignore

from cmdq.cmdproc import BaseCmdProc

from .cmds import ScreenCmd


class CmdProc(BaseCmdProc[ScreenCmd]):
    def __init__(self):
        super().__init__()
        self._epd = epd.EPD()

    def _handle_cmd(self, cmd: ScreenCmd) -> None:
        return cmd(self._epd)
