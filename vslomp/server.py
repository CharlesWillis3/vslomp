import asyncio
from typing import Any, AsyncIterator, Awaitable, Tuple, Union

import protoflux.servicer as flux
from PIL import Image
from qcmd.core import CommandHandle

import vslomp.display.proc as disp
import vslomp.gen.vslomp as gen
import vslomp.video.proc as vid
from vslomp.video.proc import LoadResult


@flux.grpc_service("vslomp.PlayerService")
class PlayerService:
    def __init__(self, disp: disp.DisplayProcessor, vid: vid.VideoProcessor) -> None:
        self.dp = disp
        self.vp = vid

    @flux.grpc_method
    async def open(self, req: gen.Open) -> AsyncIterator[gen.OpenResult]:
        loop = asyncio.get_running_loop()

        if req.screen_path:
            ok, res = await wait_for_cmd(self.dp.send(disp.Cmd.Splashscreen(req.screen_path)))

            yield gen.OpenResult(action=gen.OpenResultAction.SPLASH_SCREEN, ok=ok, err=str(res))

        ok, res = await wait_for_cmd(
            self.vp.send(
                vid.Cmd.Load(req.video_path, req.vstream_idx if req.vstream_idx else 0, "NONKEY")
            )
        )

        if ok and isinstance(res, LoadResult):
            load_result = res
            yield gen.OpenResult(
                action=gen.OpenResultAction.LOAD_VIDEO, ok=True, frame_count=load_result.frames
            )
        else:
            yield gen.OpenResult(action=gen.OpenResultAction.LOAD_VIDEO, ok=False, err=str(res))
            return

        ok, res = await wait_for_cmd(self.dp.send(disp.Cmd.InitVideo(req.frame_wait)))

        if not ok:
            yield gen.OpenResult(action=gen.OpenResultAction.PLAY_VIDEO, ok=False, err=str(res))
            return

        iter = _FrameIterator(load_result.frames)

        def _onimage(img: Image.Image, fr: int, tags: Any):
            def __push(val: Union[int, str]):
                loop.call_soon_threadsafe(lambda: iter.push(val))

            self.dp.send(disp.Cmd.Display(img, fr), tags=tags).then(
                lambda r, t: __push(fr)
            ).or_err(lambda ex, t: __push(str(ex)))

        gen_task = wait_for_cmd(
            self.vp.send(
                vid.Cmd.GenerateImages(
                    load_result, _onimage, start=req.start, stop=req.stop, step=req.step
                )
            )
        )

        self.dp.send(disp.Cmd.FINISH, pri=100)

        async for res in iter:
            yield res

        # await gen_task

        self.vp.join()
        self.dp.join()

        yield gen.OpenResult(action=gen.OpenResultAction.PLAY_VIDEO, ok=True)


def wait_for_cmd(h: CommandHandle[Any, Any]) -> Awaitable[Tuple[bool, Union[Exception, Any]]]:
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def _result(r: Any, t: disp.disp_utils.Tags):
        loop.call_soon_threadsafe(lambda: future.set_result((True, r)))

    def _error(ex: Exception, t: disp.disp_utils.Tags):
        loop.call_soon_threadsafe(lambda: future.set_result((False, ex)))

    h.then(_result).or_err(_error)

    return future


class _FrameIterator(AsyncIterator[gen.OpenResult]):
    def __init__(self, frame_count: int):
        self._frame_count = frame_count
        self._stop = False
        self._q: "asyncio.Queue[Union[int, str]]" = asyncio.Queue()

    def __aiter__(self) -> AsyncIterator[gen.OpenResult]:
        return self

    async def __anext__(self) -> gen.OpenResult:
        if self._stop:
            raise StopAsyncIteration

        curr = await self._q.get()

        if isinstance(curr, str):
            self._stop = True
            return gen.OpenResult(action=gen.OpenResultAction.PLAY_VIDEO, ok=False, err=curr)

        if curr >= self._frame_count - 1:
            self._stop = True

        return gen.OpenResult(action=gen.OpenResultAction.PLAY_VIDEO, ok=True, frame_count=curr)

    def push(self, frame: Union[int, str]):
        self._q.put_nowait(frame)
