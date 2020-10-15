from __future__ import annotations

from enum import Enum, auto
from typing import Any, Callable

from cmdq.cmdproc import CmdProc, UnknownCmdError  # type:ignore

from .handlers._imager import (
    cmd_convert,
    cmd_load_file,
    cmd_get_demo,
    cmd_ensure_size,
    DataType,
    ReturnType,
    ConvertData,
    EnsureSizeData,
)


def _raise_unknown(cmd: Any) -> Callable[[DataType], ReturnType]:
    def _inner(_data: DataType) -> ReturnType:
        try:
            raise UnknownCmdError(cmd)
        finally:
            return None

    return _inner

class ImagerCmdData:
    convert = ConvertData
    ensure_size = EnsureSizeData

class ImagerCmd(Enum):
    LOAD_FILE = auto()  # str -> Image
    CONVERT = auto()  # ConvertData -> Image
    GET_DEMO = auto() # -> Image
    ENSURE_SIZE = auto() # EnsureSizeData -> Image


class ImagerCmdProc(CmdProc[ImagerCmd]):
    _handlers = {
        ImagerCmd.LOAD_FILE: cmd_load_file,
        ImagerCmd.CONVERT: cmd_convert,
        ImagerCmd.GET_DEMO: cmd_get_demo,
        ImagerCmd.ENSURE_SIZE: cmd_ensure_size
    }

    async def _handle_msg(self, cmd: ImagerCmd, data: DataType) -> ReturnType:
        return self._handlers.get(cmd, _raise_unknown(cmd))(data)