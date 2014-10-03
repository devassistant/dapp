import pytest
import yaml

from dapp import update_ctxt, protocol_version, DAPPCommunicator, DAPPException, \
    DAPPBadMsgType, DAPPBadProtocolVersion

class TestUpdateCtxt(object):
    @pytest.mark.parametrize('old, new', [
        ({'a': 'a', 'b': 'b'}, {}),
        ({'a': 'a'}, {'b': 'b'}),
        ({}, {'a': 'a', 'b': 'b'}),
        ({'a': 'a'}, {'a': 'aa', 'b': 'bb'}),
    ])
    def test_update_ctxt(self, old, new):
        update_ctxt(old, new)
        assert old == new

    def test_update_ctxt_ignores_assistant(self):
        old = {'__assistant__': ''}
        update_ctxt(old, {})
        assert old == {'__assistant__': ''}

class TestDAPPCommunicator(object):
    def setup_method(self, method):
        self.dc = DAPPCommunicator()

    def test_dump_ctxt(self):
        ctxt = {'__assistant__': 'spam', '__magic__': 'tadaaa',
                'some': 'value', 'some': 'othervalue'}
        res = yaml.load(self.dc._dump_ctxt(ctxt))
        ctxt.pop('__assistant__')
        assert {'ctxt': ctxt} == res

    @pytest.mark.parametrize('msg, allowed_types, exctype', [
        ('not a mapping', None, DAPPException),
        ({'no_msg_type': 'foo'}, None, DAPPException),
        ({'msg_type': 'present', 'but no': 'ctxt'}, None, DAPPException),
        ({'msg_type': 'foo', 'ctxt': {}}, ['bar'], DAPPBadMsgType),
        ({'msg_type': 'foo', 'ctxt': {}, 'dapp_protocol_version': 'foo'}, None,
            DAPPBadProtocolVersion),
    ])
    def test_check_loaded_msg(self, msg, allowed_types, exctype):
        with pytest.raises(exctype):
            self.dc._check_loaded_msg(msg, allowed_types)

    def test_compose_msg(self):
        msg = self.dc._compose_msg(ctxt={'foo': 'bar'}, data={'spam': 'spam'})
        expected_lines = set([b'START', b'STOP', b'ctxt:', b'  foo: bar', b'spam: spam',
            b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"'])
        assert set(msg.splitlines()) == expected_lines

    @pytest.mark.parametrize('lst, res_from, res_to', [
        (['', 'START', 'dapp_protocol_version: 1', 'ctxt', '  foo: bar',
          'spam: spam', 'STOP', ''], 2, -2),
        (['', ''], -1, -1)
    ])
    def test_msg_from_start_stop_list(self, lst, res_from, res_to):
        msg = self.dc._msg_from_start_stop_list(lst)
        if res_from > 0:
            assert msg == '\n'.join(lst[res_from:res_to])
        else:
            assert msg == None

    @pytest.mark.parametrize('lst', [
        ['asd', 'START', 'STOP'],
        ['START', 'STOP', 'asd'],
        ['STOP', 'asd'],
        ['START', 'asd'],
    ])
    def test_msg_from_start_stop_wrong_input(self, lst):
        with pytest.raises(DAPPException):
            self.dc._msg_from_start_stop_list(lst)
