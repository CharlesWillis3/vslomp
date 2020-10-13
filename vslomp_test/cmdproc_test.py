import pytest
from enum import Enum
from vslomp.cmdproc import *

class XCmd(Enum):
    ONE = 1,
    TWO = 2

class XProc(CmdProc[XCmd]):
    async def _handle_msg(self, cmd: TCmd, data: int) -> int:
        if cmd == XCmd.ONE:
            return data * 1
        elif cmd == XCmd.TWO:
            return data * 2
        else: raise ValueError()

def raise_error(_: MsgHandle[XCmd], ex: Exception):
    assert not ex

@pytest.mark.asyncio
async def test_send():
    x = XProc(onerror=raise_error)
    await x.start()
    await x.send(XCmd.ONE, 1)
    await x.join()