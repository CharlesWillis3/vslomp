import asyncio
from asyncio.tasks import wait_for
from os import wait
from queue import Queue
from typing import Any, AsyncIterator, Container, Optional, Tuple, Union

import protoflux.servicer as flux
from PIL import Image
from qcmd.core import CommandHandle

import vslomp.display.proc as disp
import vslomp.gen.vslomp as gen
import vslomp.video.proc as vid


@flux.grpc_service("vslomp.PlayerService")
class PlayerService:
    curr_vid: Optional[vid.LoadResult] = None

    def __init__(self, disp: disp.DisplayProcessor, vid: vid.VideoProcessor) -> None:
        self.dp = disp
        self.vp = vid

    @flux.grpc_method
    async def show_screen(self, req: gen.ShowScreen) -> gen.ShowScreenResult:

        h = self.dp.send(disp.Cmd.Splashscreen((req.screen_path)), pri=46)

        ok, err = await wait_for_cmd(h)

        return gen.ShowScreenResult(gen.Result(ok=ok, err=err))

    @flux.grpc_method
    async def load_video(self, req: gen.LoadVideo) -> gen.LoadVideoResult:
        event = asyncio.Event()
        frames = 0
        err = None

        def _generate(res: vid.LoadResult, _: Any):
            nonlocal frames
            frames = res.frames
            self.curr_vid = res
            event.set()

        def _error(ex: Exception, _: Any):
            nonlocal err
            err = str(ex)
            event.set()

        h = self.dp.send(disp.Cmd.InitVideo(wait=req.frame_wait))
        ok, err = await wait_for_cmd(h)

        if not ok:
            return gen.LoadVideoResult(result=gen.Result(ok=ok, err=err))

        self.vp.send(
            vid.Cmd.Load(
                req.video_path,
                vstream_idx=req.vstream_idx,
                skip_frame="NONKEY",
            )
        ).then(_generate).or_err(_error)

        await event.wait()

        if err is None:
            return gen.LoadVideoResult(frame_count=frames, result=gen.Result(ok=True))
        else:
            return gen.LoadVideoResult(result=gen.Result(ok=False, err=err))

    @flux.grpc_method
    async def play(self, req: gen.Play) -> AsyncIterator[gen.PlayResult]:
        if self.curr_vid is None:
            yield gen.PlayResult(done=True, result=gen.Result(ok=False, err="Video Not Loaded"))
            return

        generator = _FrameIterator(self.curr_vid.frames)

        def _onimage(img: Image.Image, frame: int, tags: Container[Any]):
            generator.push(frame)
            self.dp.send(disp.Cmd.Display(img, frame), tags=[("frame", frame)])

        def _result(_: Any, __: Any):
            self.vp.send(vid.Cmd.Unload())
            self.vp.join()

        def _error(ex: Exception, _: Any):
            generator.push(str(ex))

        self.vp.send(
            vid.Cmd.GenerateImages(
                self.curr_vid, _onimage, start=req.start, stop=req.stop, step=req.step
            )
        ).then(_result).or_err(_error)

        async for m in generator:
            yield m

    @flux.grpc_method
    async def unload(self, req: gen.Unload) -> gen.UnloadResult:
        ...


async def wait_for_cmd(h: CommandHandle[Any, Any]) -> Tuple[bool, str]:
    event = asyncio.Event()
    err = None

    def _result(r: Any, t: disp.disp_utils.Tags):
        event.set()

    def _error(ex: Exception, t: disp.disp_utils.Tags):
        nonlocal err
        err = str(ex)
        event.set()

    h.then(_result).or_err(_error)

    await event.wait()

    return (err is not None, err or "")


class _FrameIterator(AsyncIterator[gen.PlayResult]):
    _q: "asyncio.Queue[Union[int, str]]" = asyncio.Queue()

    def __init__(self, frame_count: int):
        self.frame_count = frame_count
        self._stop = False

    def __aiter__(self) -> AsyncIterator[gen.PlayResult]:
        return self

    async def __anext__(self) -> gen.PlayResult:
        if self._stop:
            raise StopAsyncIteration

        curr = await self._q.get()

        if isinstance(curr, str):
            self._stop = True
            return gen.PlayResult(result=gen.Result(ok=False, err=curr))

        if curr == self.frame_count - 1:
            self._stop = True

        return gen.PlayResult(frame_idx=curr, done=self._stop, result=gen.Result(ok=True))

    def push(self, frame: Union[int, str]):
        self._q.put_nowait(frame)
