from __future__ import annotations

import asyncio
import concurrent.futures
import enum
import logging
import threading
import time
from abc import ABC, abstractmethod
from queue import PriorityQueue
from types import TracebackType
from typing import (
    Any,
    Callable,
    ClassVar,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from .exceptions import CmdProcError, ResultCallbackError

TCmd = TypeVar("TCmd")


class CmdHandle(Generic[TCmd]):
    def __init__(self, tcmd: Type[TCmd], pri: int, entry: int, tags: Optional[List[Any]]) -> None:
        self._tcmd = tcmd
        self._pri = pri
        self._entry = entry
        self._tags = tags if tags else []

    def __lt__(self, ls: CmdHandle[TCmd]) -> bool:
        return self.pri < ls.pri if self.pri != ls.pri else self.entry < ls.entry

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.tcmd} pri={self.pri} entry={self.entry} tags={self.tags} at {id(self)}>"

    @property
    def tcmd(self) -> Type[TCmd]:
        return self._tcmd

    @property
    def pri(self) -> int:
        return self._pri

    @property
    def entry(self) -> int:
        return self._entry

    @property
    def tags(self) -> List[Any]:
        return self._tags


class _ProcControl(enum.Enum):
    BREAK = enum.auto()


_ResultCallback = Callable[[CmdHandle[TCmd], Optional[Any]], Optional[Any]]
_ErrorCallback = Callable[[CmdHandle[TCmd], Exception], None]

_logger = logging.getLogger(__name__)


def _logevent(evt: str, msg: Any, detail: Any = None) -> None:
    _logger.info(f"""{evt:5} {time.time():020.7f} {msg}""")
    if detail:
        _logger.info(f"""\t{detail}""")


class BaseCmdProc(ABC, Generic[TCmd]):
    _QueueEntry = Union[Tuple[CmdHandle[TCmd], TCmd], Tuple[CmdHandle[_ProcControl], Any]]
    _ProcControlHandle: ClassVar[CmdHandle[_ProcControl]] = CmdHandle[_ProcControl](
        type(_ProcControl), 0, 0, None
    )

    def __init__(
        self,
        onresult: Optional[_ResultCallback[TCmd]] = None,
        onerror: Optional[_ErrorCallback[TCmd]] = None,
    ) -> None:
        self.__entry = 1  # entry=0 is reserved for control commands
        self._onresult = onresult
        self._onerror = onerror
        self.__q: PriorityQueue[BaseCmdProc._QueueEntry] = PriorityQueue()
        self.__qevent = threading.Event()
        self.__qexecutor = concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix=str(self.__class__)
        )
        self.__qtask: asyncio.Future[None] = cast(
            asyncio.Future,  # type:ignore
            asyncio.get_event_loop().run_in_executor(
                self.__qexecutor,
                self.__consume,
            ),
        )

    def __enter__(self) -> BaseCmdProc[TCmd]:
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self.halt()
        if __exc_type == CmdProcError:
            return True

        return False

    def on_result(self, cb: _ResultCallback[TCmd]) -> BaseCmdProc[TCmd]:
        self._onresult = cb
        return self

    def on_error(self, cb: _ErrorCallback[TCmd]) -> BaseCmdProc[TCmd]:
        self._onerror = cb
        return self

    def start(self) -> None:
        self.__qevent.set()

    def pause(self) -> None:
        self.__qevent.clear()

    def join(self) -> None:
        self.__q.join()

    def halt(self) -> None:
        if self.__qtask.done():
            return

        _logevent("HALT", self)
        self.__q.put((BaseCmdProc._ProcControlHandle, _ProcControl.BREAK))
        if not self.__qevent.is_set():
            self.__qevent.set()

        self.__qexecutor.shutdown(wait=True)

    def send(
        self, cmd: Union[TCmd, Type[TCmd]], pri: int = 50, tags: Optional[List[Any]] = None
    ) -> CmdHandle[TCmd]:
        tcmd = cmd if isinstance(cmd, Type) else type(cmd)
        _cmd = cmd() if isinstance(cmd, Type) else cmd
        hcmd = CmdHandle(tcmd, pri, self.__entry, tags)
        self.__entry += 1
        self.__q.put((hcmd, _cmd))
        _logevent("RECVD", hcmd)
        return hcmd

    @abstractmethod
    def _handle_cmd(self, cmd: TCmd) -> Any:
        raise NotImplementedError

    def __consume(self) -> None:
        def _exec_result(_hcmd: CmdHandle[TCmd], _res: Any):
            if callable(self._onresult):
                try:
                    self._onresult(_hcmd, _res)
                except Exception as ex:
                    raise ResultCallbackError(ex)

        while self.__qevent.wait():
            hcmd, cmd = self.__q.get(block=True, timeout=None)
            if isinstance(cmd, _ProcControl):
                if cmd == _ProcControl.BREAK:
                    break

            try:
                _logevent("START", hcmd)
                result = self._handle_cmd(cmd)
                _exec_result(hcmd, result)
            except Exception as ex:
                _logevent("ERROR", hcmd, ex)
                if callable(self._onerror):
                    self._onerror(hcmd, CmdProcError(ex))
            finally:
                self.__q.task_done()
