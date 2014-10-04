import pytest
import six
import yaml

from dapp import DAPPClient, DAPPBadMsgType, DAPPNoSuchCommand, DAPPCommandException

from test.communicator_test_case import CommunicatorTestCase

class MyClient(DAPPClient):
    def run(self, ctxt):
        self.call_command('foo', 'bar', ctxt)
        return True, 'success'


class TestClient(CommunicatorTestCase):
    """Some test methods for this class are inherited from CommunicatorTestCase,
    since they're common for both server and client.
    """
    def setup_method(self, method):
        self.lfd = six.BytesIO()
        self.wfd = six.BytesIO()
        self.c = MyClient(listen_fd=self.lfd, write_fd=self.wfd)

    def test_call_command_no_such_command(self):
        self._write_msg(self.s_no_such_cmd_msg_lines)
        with pytest.raises(DAPPNoSuchCommand):
            self.c.call_command('foo', 'bar', {})

    def test_call_command_command_exception(self):
        self._write_msg(self.s_cmd_exc_msg_lines)
        with pytest.raises(DAPPCommandException):
            self.c.call_command('foo', 'bar', {})

    def test_call_command_ok(self):
        self._write_msg(self.s_cmd_ok_msg_lines)
        d = {}
        lres, res = self.c.call_command('foo', 'bar', d)
        assert lres == True
        assert res == 'result'
        assert d == {'spam': 'spam', 'foo': 'bar'}

    def test_pingpong(self):
        # tests a single complex pingpong run on client side
        self._write_msg(self.s_run_msg_lines, seek='end')
        self._write_msg(self.s_cmd_ok_msg_lines, seek='start')
        self.c.pingpong()
        
        msgs = self._read_sent_msg().split(b'STOP\nSTART')
        call_msg = msgs[0][len('START\n'):]
        ok_msg = msgs[1][:-len('STOP\n')]
        assert yaml.load(call_msg) == self.c_call_msg_dict
        assert yaml.load(ok_msg) == self.c_ok_msg_dict
