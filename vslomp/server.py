from typing import AsyncIterator

import protoflux.servicer as flux

import vslomp.gen.vslomp as gen


@flux.grpc_service("vslomp.PlayerService")
class PlayerService:
    def __init__(self) -> None:
        pass

    @flux.grpc_method
    async def load_video(self, req: gen.LoadVideo) -> gen.LoadVideoResult:
        ...

    @flux.grpc_method
    async def play(self, req: gen.Play) -> AsyncIterator[gen.PlayResult]:
        ...

    @flux.grpc_method
    async def unload(self, req: gen.Unload) -> gen.UnloadResult:
        ...
