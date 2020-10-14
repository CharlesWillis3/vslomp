import pytest
from enum import Enum
from cmdq.cmdq.cmdproc import *


class XCmd(Enum):
    ONE = 1
    TWO = 2


class XProc(CmdProc[XCmd]):
    async def _handle_msg(self, cmd: TCmd, data: int) -> int:
        if cmd == XCmd.ONE:
            return data * 1
        elif cmd == XCmd.TWO:
            return data * 2
        else:
            raise UnknownCmdError()


onerror_called: bool = False
onresult_called: bool = False
expected_msg_handle: Optional[MsgHandle[XCmd]] = None


def raise_error(h: MsgHandle[XCmd], ex: Exception):
    global onerror_called
    onerror_called = True
    assert h is expected_msg_handle
    try:
        with pytest.raises(Error):
            raise ex
    finally:
        return None


def handle_result(expected: Any) -> CmdProc.ResultCallback:
    def _inner(h: MsgHandle[XCmd], res: Optional[Any]):
        global onresult_called
        onresult_called = True

        assert h is expected_msg_handle
        assert res == expected

    return _inner


@pytest.mark.asyncio
async def test_send_result():
    global expected_msg_handle, onerror_called, onresult_called
    expected_msg_handle = None
    onerror_called = False
    onresult_called = False

    x = XProc(onerror=raise_error, onresult=handle_result((2)))
    await x.start()
    expected_msg_handle = await x.send(XCmd.ONE, 2)
    await x.join()
    assert onresult_called
    assert onerror_called == False


@pytest.mark.asyncio
async def test_send_error():
    global expected_msg_handle, onerror_called, onresult_called
    expected_msg_handle = None
    onerror_called = False
    onresult_called = False

    x = XProc(onerror=raise_error, onresult=handle_result((2)))
    await x.start()
    expected_msg_handle = await x.send(XCmd.TWO, pri=5)
    assert expected_msg_handle.pri == 5
    await x.join()
    assert onerror_called
    assert onresult_called == False

def test_handle_pri():
    x = MsgHandle[XCmd](XCmd.ONE, 1)
    y = MsgHandle[XCmd](XCmd.TWO, 2)

    assert x < y
    assert y != x

@pytest.mark.asyncio
async def test_bad_cmd():
    global expected_msg_handle
    x = XProc(onerror=raise_error)
    await x.start()
    expected_msg_handle = await x.send(1, None) # type:ignore
    await x.join()
    assert onerror_called