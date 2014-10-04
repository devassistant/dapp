import six
import yaml

from dapp import DAPPServer

from test.communicator_test_case import CommunicatorTestCase

class MockProcess(object):
    def __init__(self):
        self.stdin = six.BytesIO()
        self.stdout = six.BytesIO()

class TestServer(CommunicatorTestCase):
    def setup_method(self, method):
        proc = MockProcess()
        self.wfd = proc.stdin
        self.lfd = proc.stdout
        self.s = DAPPServer(proc=proc)

    def test_send_msg(self):
        self.s.send_msg('type', ctxt={'foo': 'bar'}, data={'spam': 'spam'})
        msg = self._read_sent_msg()
        assert set(msg.splitlines()) == set(self.some_msg_lines)
