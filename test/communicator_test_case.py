import pytest

from dapp import protocol_version, DAPPBadMsgType

class CommunicatorTestCase(object):
    # a custom message that can be sent by either client or server
    some_msg_lines = [b'START', b'ctxt:', b'  foo: bar', b'spam: spam',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"',
        b'msg_type: type', b'STOP']
    some_msg_dict = {'ctxt': {'foo': 'bar'}, 'spam': 'spam', 'msg_type': 'type',
        'dapp_protocol_version': str(protocol_version)}

    # client calling a command
    c_call_msg_lines = [b'START', b'ctxt:', b'  spam: spam', b'msg_type: call_command',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"',
        b'command_type: foo', b'command_input: bar', b'STOP']
    c_call_msg_dict = {'ctxt': {'spam': 'spam'}, 'msg_type': 'call_command',
        'command_type': 'foo', 'command_input': 'bar',
        'dapp_protocol_version': str(protocol_version)}

    # the 3 below are various responses to c_call_msg_lines
    s_no_such_cmd_msg_lines = [b'START', b'ctxt:', b'  foo: bar',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"',
        b'msg_type: no_such_command', b'STOP']

    s_cmd_exc_msg_lines = [b'START', b'ctxt:', b'  foo: bar',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"',
        b'msg_type: command_exception', b'exception: problem', b'STOP']

    s_cmd_ok_msg_lines =  [b'START', b'ctxt:', b'  spam: spam', b'  foo: bar',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"',
        b'msg_type: command_result', b'lres: True', b'res: result', b'STOP']

    # server telling client to start
    s_run_msg_lines = [b'START', b'ctxt:', b'  spam: spam', b'msg_type: run',
        b'dapp_protocol_version: "' + protocol_version.encode('utf8') + b'"', b'STOP']

    # client saying that it finished successfully
    c_ok_msg_dict = {'ctxt': {'foo': 'bar', 'spam': 'spam'}, 'msg_type': 'finished',
        'lres': True, 'res': 'success', 'dapp_protocol_version': str(protocol_version)}

    def _read_sent_msg(self, from_pos=0, nbytes=-1):
        where = self.wfd.tell()
        self.wfd.seek(from_pos)
        b = self.wfd.read(nbytes)
        self.wfd.seek(where)
        return b

    def _write_msg(self, msg, seek='where'):
        if isinstance(msg, list):
            msg = b'\n'.join(msg)
        where = self.lfd.tell()
        if not msg.endswith(b'\n'):
            msg = msg + b'\n'
        self.lfd.write(msg)
        if seek == 'where':
            self.lfd.seek(where, 0)
        elif seek == 'start':
            self.lfd.seek(0, 0)
        else:  # end
            self.lfd.seek(0, 2)

    def test_send_msg(self):
        self.c.send_msg('type', ctxt={'foo': 'bar'}, data={'spam': 'spam'})
        msg = self._read_sent_msg()
        assert set(msg.splitlines()) == set(self.some_msg_lines)
        
    def test_recv_msg(self):
        self._write_msg(self.some_msg_lines)
        msg = self.c.recv_msg()
        assert msg == self.some_msg_dict

    def test_recv_msg_wrong_type(self):
        # we don't test various malformed messages here; they're checked
        #  by test_check_loaded_msg in test_general
        self._write_msg(self.some_msg_lines)
        with pytest.raises(DAPPBadMsgType):
            self.c.recv_msg(allowed_types=['foo'])
