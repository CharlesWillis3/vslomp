from __future__ import annotations

from enum import Enum, auto
from typing import Any, Callable

from cmdq.cmdproc import CmdProc, UnknownCmdError  # type:ignore

from .handlers._imager import (
    cmd_convert,
    cmd_load_file,
    cmd_get_demo,
    DataType,
    ReturnType,
    ConvertData, # type:ignore
)


def _raise_unknown(cmd: Any) -> Callable[[DataType], ReturnType]:
    def _inner(_data: DataType) -> ReturnType:
        try:
            raise UnknownCmdError(cmd)
        finally:
            return None

    return _inner


class ImagerCmd(Enum):
    LOAD_FILE = auto()  # str -> Image
    CONVERT = auto()  # ConvertData -> Image
    GET_DEMO = auto()


class ImagerCmdProc(CmdProc[ImagerCmd]):
    _handlers = {
        ImagerCmd.LOAD_FILE: cmd_load_file,
        ImagerCmd.CONVERT: cmd_convert,
        ImagerCmd.GET_DEMO: cmd_get_demo,
    }

    async def _handle_msg(self, cmd: ImagerCmd, data: DataType) -> ReturnType:
        return self._handlers.get(cmd, _raise_unknown(cmd))(data)