import six
import yaml

from dapp import DAPPServer

from test.communicator_test_case import CommunicatorTestCase

class MockProcess(object):
    def __init__(self):
        self.stdin = six.BytesIO()
        self.stdout = six.BytesIO()

    def poll(self):
        return None

class TestServer(CommunicatorTestCase):
    """Some test methods for this class are inherited from CommunicatorTestCase,
    since they're common for both server and client.
    """
    def setup_method(self, method):
        proc = MockProcess()
        self.wfd = proc.stdin
        self.lfd = proc.stdout
        self.c = DAPPServer(proc=proc)
