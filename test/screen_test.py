import pytest
import logging
from vslomp.display.screen import *

LOG = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_screen_init():
    result_handles = []
    error_handles = []

    s = ScreenCmdProc()
    await s.on_error(lambda h, ex: error_handles.append(h))
    await s.on_result(lambda h, res: result_handles.append(h))
    LOG.info("starting")
    await s.start()
    LOG.info("sending INIT")
    s1 = await s.send(pri=25, cmd=ScreenCmd.INIT)
    LOG.info("sending CLEAR")
    s2 = await s.send(pri=25, cmd=ScreenCmd.CLEAR)
    LOG.info("sending SLEEP")
    s3 = await s.send(pri=50, cmd=ScreenCmd.SLEEP)
    LOG.info("joining")
    await s.join()
    LOG.info("asserting")
    assert s1 in result_handles
    assert s2 in result_handles
    assert s3 in result_handles
    assert len(error_handles) == 0
    LOG.info("returning")
    
    import asyncio
    asyncio.get_running_loop().stop()
    return None