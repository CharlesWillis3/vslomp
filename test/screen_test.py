import logging
from cmdq.cmdproc import CmdProcError # type:ignore

import pytest

from vslomp.display.screen import *

LOG = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_screen_init():
    import asyncio

    result_handles = []
    error_handles = []

    async def append_result(h, res):  # type:ignore
        result_handles.append(h) # type:ignore

    s = ScreenCmdProc()
    await s.on_error(lambda h, ex: error_handles.append(h))
    await s.on_result(append_result) # type:ignore
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
    
    asyncio.get_running_loop().stop()

@pytest.mark.asyncio
async def test_screen_display_data():
    results = []
    errors = []

    async def append_result(h, res):  # type:ignore
        results.append((h, res)) # type:ignore

    s = ScreenCmdProc()
    await s.on_error(lambda h, ex: errors.append((h, ex)))
    await s.on_result(append_result) # type:ignore
    await s.start()
    msgh = await s.send(ScreenCmd.DISPLAY, None)
    await s.join()
    assert len(errors) == 1
    rh, rex = errors[0]
    assert rh is msgh
    assert isinstance(rex, CmdProcError)

    import asyncio
    asyncio.get_running_loop().stop()