from __future__ import annotations

from typing import Any

from cmdq.cmdproc import BaseCmdProc

from .cmds import ImagerCmd


class CmdProc(BaseCmdProc[ImagerCmd]):
    def _handle_cmd(self, cmd: ImagerCmd) -> Any:
        return cmd()