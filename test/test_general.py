import pytest

from dapp import update_ctxt, DAPPCommunicator

class TestUpdateCtxt(object):
    @pytest.mark.parametrize('old, new', [
        ({'a': 'a', 'b': 'b'}, {}),
        ({'a': 'a'}, {'b': 'b'}),
        ({}, {'a': 'a', 'b': 'b'}),
        ({'a': 'a'}, {'a': 'aa', 'b': 'bb'})
    ])
    def test_update_ctxt(self, old, new):
        update_ctxt(old, new)
        assert old == new
