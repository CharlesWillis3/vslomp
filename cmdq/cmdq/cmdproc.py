from __future__ import annotations

import asyncio
import concurrent.futures
import threading
import time
from abc import ABC, abstractmethod
from operator import __lt__
from queue import PriorityQueue
from typing import Any, Callable, Generic, Optional, Tuple, Type, TypeVar, Union, cast

from .exceptions import CmdProcError, ResultCallbackError

TCmd = TypeVar("TCmd")


class CmdHandle(Generic[TCmd]):
    def __init__(self, tcmd: Type[TCmd], pri: int, entry: int, *tags: Any) -> None:
        self._tcmd = tcmd
        self._pri = pri
        self._entry = entry
        self._tags = tags

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
    def tags(self) -> Any:
        return self._tags


_ResultCallback = Callable[[CmdHandle[TCmd], Optional[Any]], Optional[Any]]
_ErrorCallback = Callable[[CmdHandle[TCmd], Exception], None]
_QueueEntry = Tuple[CmdHandle[TCmd], TCmd]


class BaseCmdProc(ABC, Generic[TCmd]):
    def __init__(
        self,
        onresult: Optional[_ResultCallback[TCmd]] = None,
        onerror: Optional[_ErrorCallback[TCmd]] = None,
    ) -> None:
        self.__entry = 0
        self._onresult = onresult
        self._onerror = onerror
        self.__q: PriorityQueue[_QueueEntry] = PriorityQueue()
        self.__qevent = threading.Event()
        self.__qexecutor = concurrent.futures.ThreadPoolExecutor(thread_name_prefix=str(self.__class__))
        self.__qtask : asyncio.Future[None] = cast(
            asyncio.Future, # type:ignore
            asyncio.get_event_loop().run_in_executor(
                self.__qexecutor,
                self.__consume,
            ),
        )

    def __del__(self) -> None:
        self.__qtask.cancel()
        self.__qexecutor.shutdown()

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

    def cancel(self) -> bool:
        return self.__qtask.cancel()

    def send(
        self, cmd: Union[TCmd, Type[TCmd]], pri: int = 50, *tags: Any
    ) -> CmdHandle[TCmd]:
        tcmd = cmd if isinstance(cmd, Type) else type(cmd)
        _cmd = cmd() if isinstance(cmd, Type) else cmd
        hcmd = CmdHandle(tcmd, pri, self.__entry, tags)
        self.__entry += 1
        self.__q.put((hcmd, _cmd))
        print("RECVD", time.time(), hcmd)
        return hcmd

    @abstractmethod
    def _handle_cmd(self, cmd: TCmd) -> Optional[Any]:
        raise NotImplementedError

    def __consume(self) -> None:
        def _exec_result(_hcmd: CmdHandle[TCmd], _res: Optional[Any]):
            if callable(self._onresult):
                try:
                    self._onresult(_hcmd, _res)
                except Exception as ex:
                    raise ResultCallbackError(ex)

        while self.__qevent.wait():
            hcmd, cmd = self.__q.get(block=True, timeout=None)

            try:
                print("START", time.time(), hcmd)
                result = self._handle_cmd(cmd)
                _exec_result(hcmd, result)
            except Exception as ex:
                if callable(self._onerror):
                    self._onerror(hcmd, CmdProcError(ex))
                else:
                    raise
            finally:
                self.__q.task_done()