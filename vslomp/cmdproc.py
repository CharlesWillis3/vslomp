from __future__ import annotations
import asyncio
from asyncio.queues import PriorityQueue
from typing import Any, Awaitable, Callable, Generic, NoReturn, Optional, Tuple, TypeVar, Union


class Error(Exception):
    pass


class ResultCallbackError(Error):
    pass


TCmd = TypeVar("TCmd")


class MsgHandle(Generic[TCmd]):
    def __init__(self, cmd: TCmd, pri: int):
        self.cmd = cmd
        self.pri = pri


class CmdProc(Generic[TCmd]):
    ResultCallback = Callable[[MsgHandle[TCmd], Optional[Any]], None]
    ErrorCallback = Callable[[MsgHandle[TCmd], Exception], Union[None,NoReturn]]

    def __init__(self, onresult: Optional[ResultCallback] = None, onerror: Optional[ErrorCallback] = None):
        self._onresult = onresult
        self._onerror = onerror
        self.__isrunning_lock = asyncio.Lock()
        self.__isrunning = False
        self._q: PriorityQueue[Tuple[int, MsgHandle[TCmd], Optional[Any]]] = asyncio.PriorityQueue()
        self._consume_task = asyncio.create_task(self.__consume())

    async def start(self):
        async with self.__isrunning_lock:
            self.__isrunning = True

    async def pause(self):
        async with self.__isrunning_lock:
            self.__isrunning = False

    async def send(self, cmd: TCmd, data: Optional[Any] = None, pri: int = 50) -> MsgHandle[TCmd]:
        h = MsgHandle(cmd, pri)
        await self._q.put((pri, h, data))
        return h

    async def join(self) -> bool:
        await self._q.join()
        return self._consume_task.cancel()

    def _handle_msg(self, cmd: TCmd, data: Optional[Any]) -> Awaitable[Optional[Any]]:
        raise NotImplementedError()

    async def __is_running(self) -> bool:
        async with self.__isrunning_lock:
            return self.__isrunning

    async def __consume(self) -> None:
        while True:
            if await self.__is_running():
                _, hmsg, data = await self._q.get()
                try:
                    result = await self._handle_msg(hmsg.cmd, data)
                    if callable(self._onresult):
                        try:
                            self._onresult(hmsg, result)
                        except Exception as oresex:
                            raise ResultCallbackError(oresex)
                except Exception as ex:
                    if callable(self._onerror):
                        self._onerror(hmsg, Error(ex))
                    else:
                        raise
                finally:
                    self._q.task_done()