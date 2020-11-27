import asyncio

from grpclib.client import Channel

from vslomp.gen.vslomp import PlayerServiceStub

screen_path = "/home/pi/images/001.jpg"
video_path = "/home/pi/video/BATMAN_V_SUPERMAN_DAWN_OF_JUSTICE_TRAILER_6A_480.mov"
frame_wait = 3600
start = 10
step = 5


async def main(*, host: str, port: int):
    chan = Channel(host=host, port=port)
    player = PlayerServiceStub(chan)

    async for res in player.open(
        screen_path=screen_path,
        video_path=video_path,
        vstream_idx=0,
        frame_wait=frame_wait,
        start=start,
        step=step,
    ):
        print(res.action, res.ok, res.err, res.frame_count)

    chan.close()
    print("closed")


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--host", default="0.0.0.0")
    arg_parser.add_argument("--port", default=50051)

    args = arg_parser.parse_args()
    asyncio.run(main(host=args.host, port=args.port))
