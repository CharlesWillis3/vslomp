# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: player.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import betterproto
import grpclib


class OpenResultAction(betterproto.Enum):
    UNKNOWN = 0
    SPLASH_SCREEN = 1
    LOAD_VIDEO = 2
    PLAY_VIDEO = 3


@dataclass(eq=False, repr=False)
class Open(betterproto.Message):
    screen_path: Optional[str] = betterproto.message_field(1, wraps=betterproto.TYPE_STRING)
    video_path: str = betterproto.string_field(2)
    vstream_idx: Optional[int] = betterproto.message_field(3, wraps=betterproto.TYPE_UINT32)
    frame_wait: float = betterproto.float_field(4)
    start: Optional[int] = betterproto.message_field(5, wraps=betterproto.TYPE_INT32)
    stop: Optional[int] = betterproto.message_field(6, wraps=betterproto.TYPE_INT32)
    step: Optional[int] = betterproto.message_field(7, wraps=betterproto.TYPE_INT32)

    def __post_init__(self) -> None:
        super().__post_init__()


@dataclass(eq=False, repr=False)
class OpenResult(betterproto.Message):
    action: "OpenResultAction" = betterproto.enum_field(1)
    ok: bool = betterproto.bool_field(2)
    err: str = betterproto.string_field(3)
    frame_count: int = betterproto.uint32_field(4, group="data")

    def __post_init__(self) -> None:
        super().__post_init__()


class PlayerServiceStub(betterproto.ServiceStub):
    async def open(
        self,
        *,
        screen_path: Optional[str] = None,
        video_path: str = "",
        vstream_idx: Optional[int] = None,
        frame_wait: float = 0.0,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ) -> AsyncIterator["OpenResult"]:

        request = Open()
        if screen_path is not None:
            request.screen_path = screen_path
        request.video_path = video_path
        if vstream_idx is not None:
            request.vstream_idx = vstream_idx
        request.frame_wait = frame_wait
        if start is not None:
            request.start = start
        if stop is not None:
            request.stop = stop
        if step is not None:
            request.step = step

        async for response in self._unary_stream(
            "/vslomp.PlayerService/Open",
            request,
            OpenResult,
        ):
            yield response
