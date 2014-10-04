# -*- coding: utf-8 -*-
import logging
import sys

import six
import yaml

__version__ = "0.1.0"
protocol_version = "1"

class DAPPException(BaseException):
    pass

class DAPPBadMsgType(DAPPException):
    pass

class DAPPBadProtocolVersion(DAPPException):
    pass

class DAPPNoSuchCommand(DAPPException):
    pass

class DAPPCommandException(DAPPException):
    pass

ctxt_ignore = ['__assistant__']

def update_ctxt(old, new):
    """This method works much like dict.update, but it also deletes keys from old dict
    that are not in new dict.
    """
    allkeys = set(old.keys()) | set(new.keys())
    for k in allkeys:
        if k in ctxt_ignore:
            continue
        elif k not in new:
            del old[k]
        else:
            old[k] = new[k]

class DAPPCommunicator(object):
    def __init__(self, protocol_version=protocol_version, logger=None):
        self.protocol_version = protocol_version
        self.logger=logger

    def send_msg(self, msg_type, ctxt, data=None):
        """Send a message to the other communicating side through the pipe.

        Args:
            ctxt: global variable context from Yaml DSL
            msg_type: type of message (e.g. what this message means)
            data: dict of extra data, depends on msg_type

        Raises:
            DAPPException if something goes wrong while message is being sent
        """
        raise NotImplementedError()

    def recv_msg(self, allowed_types=None):
        """Receive a message to the other communicating side through the pipe.

        Args:
            allowed_types: list of allowed types or None; if None is specified, then any message
                type is accepted; if a list of types is specified and message type is not in
                the list, DAPPBadMsgType is raised

        Return:
            dict of decoded data sent through the pipe by the other side

        Raises:
            DAPPException if something goes wrong while message is being sent or
                if the message is malformed
            DAPPBadMsgType if msg_type is not in allowed_types and allowed_types is not None
            DAPPBadProtocolVersion if sent message has unsupported protocol version
        """
        raise NotImplementedError()

    def log(self, level, msg):
        """Log a message at given level, assuming self.logger is set,
        do nothing otherwise.
        """
        if self.logger:
            self.logger.log(level, msg)

    def _compose_msg(self, ctxt=None, data=None):
        """Compose a message to send through the pipe.
        Note: This method expects that we're not sending binary data. If someone ever needs
        to do this (I don't think so, but...), this will have to be seriously rethought.

        Args:
            ctxt: global variable context from Yaml DSL
            data: extra data to include in the message

        Returns:
            utf8 encoded message that can be sent through the pipe
        """
        msg = ['START']
        msg.append('dapp_protocol_version: "{v}"'.format(v=self.protocol_version))
        if ctxt is not None:
            msg.append(self._dump_ctxt(ctxt).strip())
        if data is not None:
            if not isinstance(data, dict):
                raise TypeError('msg must be a dict')
            msg.append(yaml.dump(data, default_flow_style=False).strip())
        msg.append('STOP\n')

        # all parts of message should be unencoded at this point
        return '\n'.join(msg).encode('utf8')

    def _msg_from_start_stop_list(self, lst):
        """Check a list of lines of received message and return a string without
        "START" and "STOP" and possibly empty lines in the beginning and end.

        Args:
            lst: list of lines of the message as read from the pipe, including
                "START" and "STOP" and possibly empty lines before and after

        Returns:
            string containing the whole message without "START" and "STOP"

        Raises:
            DAPPException if the message is somehow malformed
        """
        start_from = -1
        stop_at = -1
        for i, l in enumerate(lst):
            if l == 'START':
                start_from = i + 1
            elif start_from == -1 and l != '':
                raise self._wrong_subprocess_msg_error(lst, 'Nonempty line before "START" keyword')
            if l == 'STOP':
                stop_at = i
            elif stop_at != -1 and l != '':
                raise self._wrong_subprocess_msg_error(lst, 'Nonempty line after "STOP" keyword')

        if start_from == -1 and stop_at == -1:
            # just empty lines, this is OK => return None
            return None

        # "start_from == -1" can't happen, because it would either be caught in the loop
        #  if a non empty line was before it; otherwise both start_from and stop_at are -1
        #  and that is handled in the condition above
        if stop_at == -1:
            raise self._wrong_subprocess_msg_error(lst, 'No "STOP" keyword found in message')

        return '\n'.join(lst[start_from:stop_at])

    def _wrong_subprocess_msg_error(self, msg_lst, extra=''):
        """A helper function that formats malformed message errors with some extra info."""
        if extra:
            extra = ' ({0})'.format(extra)
        err = ['Wrong DAPP message{0}:'.format(extra)]
        err.extend(msg_lst)
        return DAPPException('\n'.join(err))

    def _dump_ctxt(self, ctxt):
        """Dump a Yaml DSL context into dict.

        Args:
            ctxt: the whole Yaml DSL context

        Returns:
            dict with one key "ctxt" and value which contains the whole dumped context;
            keys listed in global variable ctxt_ignore are always omitted from the context
        """
        dumped = {'ctxt': {}}
        for k, v in ctxt.items():
                # exclude unwanted keys
            if k not in ctxt_ignore:
                dumped['ctxt'][k] = v
        # we want to produce unencoded string here (e.g. unicode in py2, str in py3)
        #  so we need to pass encoding=None
        #  http://pyyaml.org/wiki/PyYAMLDocumentation#Python3support
        return yaml.dump(dumped, encoding=None, default_flow_style=False)

    def _check_loaded_msg(self, msg, allowed_types):
        """Does sanity checking of the message, checks that it has a proper type and
        protocol version.

        Raises:
            DAPPException if the message is not a dict or does not contain "msg_type" or "ctxt"
            DAPPBadMsgType if msg_type is not in allowed_types and allowed_types is not None
            DAPPBadProtocolVersion if sent message has unsupported protocol version
        """
        if not isinstance(msg, dict):
            raise DAPPException('PingPong message not a mapping.')
        if 'msg_type' not in msg:
            raise DAPPException('PingPong message doesn\'t contain "msg_type".')
        if 'ctxt' not in msg:
            raise DAPPException('PingPong message doesn\'t contain "ctxt".')
        if allowed_types is not None and msg['msg_type'] not in allowed_types:
            raise DAPPBadMsgType('Expected one of "{at}" message types, got "{mt}".'.\
                format(at=', '.join(allowed_types), mt=msg['msg_type']))
        # for now, let's be very strict about the protocol version
        other_pv = msg.get('dapp_protocol_version', 'none')
        if other_pv != self.protocol_version:
            err = 'PingPong client needs protocol version "{sv}", but server sent "{ov}"'.\
                format(sv=self.protocol_version, ov=other_pv)
            raise DAPPBadProtocolVersion(err)


class DAPPServer(DAPPCommunicator):
    """Class implementing server side of the PingPong protocol.
    Note: unlike DAPPClient, this class doesn't implement any sort of pingpong or run
    method, it's supposed to be used "as a library" on the DevAssistant side.
    """
    def __init__(self, proc, protocol_version=protocol_version, logger=None):
        super(DAPPServer, self).__init__(protocol_version, logger)
        self.proc = proc

    def send_msg(self, msg_type, ctxt=None, data=None):
        # TODO: check msg_type and data? we probably trust ourselves that we're sending a
        #  properly formed message, so let's not check anything here for now
        send_msg = {'msg_type': msg_type}
        if data:
            send_msg.update(data)
        msg = self._compose_msg(ctxt, data=send_msg)
        self.log(logging.DEBUG, 'Sending message to PingPong subprocess:\n' + msg.decode('utf8'))
        try:
            self.proc.stdin.write(msg)
            self.proc.stdin.flush()
        except IOError as e:
            msg = 'Error writing data to PingPong subprocess: {0}\n'.format(e)
            out = self._try_read_subprocess_error()
            if out:
                msg += 'Subprocess output:\n' + out
            raise DAPPException(msg)

    def send_msg_run(self, ctxt=None):
        """A shortcut to send "run" message."""
        self.send_msg(msg_type='run', ctxt=ctxt)

    def send_msg_command_result(self, ctxt=None, lres=False, res=''):
        self.send_msg(msg_type='command_result', ctxt=ctxt, data={'lres': lres, 'res': res})

    def send_msg_command_exception(self, ctxt=None, exception=''):
        self.send_msg(msg_type='command_exception', ctxt=ctxt, data={'exception': exception})

    def recv_msg(self, allowed_types=None):
        # throughout this method, we strip just the trailing newline
        #  from proc.stdout, since we want to get precise lines (whitespace can be significant)
        lines = []
        line = ''
        while line != 'STOP' and self.proc.poll() is None:
            # strip just the trailing newline
            line = self.proc.stdout.readline().decode('utf8')[:-1]
            lines.append(line)
        if self.proc.poll() is not None:
            # process ended, but we still haven't found STOP
            rest = self.proc.stdout.read().decode('utf8')[:-1].splitlines()
            lines.extend(rest)

        # TODO: this sometimes seems to omit some lines from the message - find out why
        self.log(logging.DEBUG,
            'Got message from PingPong subprocess:\n{0}'.format('\n'.join(lines)))
        msg = self._msg_from_start_stop_list(lines)
        if msg is None:
            return None

        parsed_yaml = yaml.load(msg)
        self._check_loaded_msg(parsed_yaml, allowed_types)
        return parsed_yaml

    def _try_read_subprocess_error(self):
        """A helper method that just tries to read the rest of subprocess output if
        something goes wrong, so that we can form a better error message."""
        try:
            return self.proc.stdout.read().decode('utf8')
        except:
            return None


class DAPPClient(DAPPCommunicator):
    """Class implementing client side of the PingPong protocol."""
    def __init__(self, listen_fd=None, write_fd=None, protocol_version=protocol_version,
            logger=None):
        super(DAPPClient, self).__init__(protocol_version, logger)
        # we want to write bytes in Python 3, so we use buffer for sys.stdin and sys.stdout
        if listen_fd:
            self.listen_fd = listen_fd
        else:
            self.listen_fd = sys.stdin if six.PY2 else sys.stdin.buffer
        if write_fd:
            self.write_fd = write_fd
        else:
            self.write_fd = sys.stdout if six.PY2 else sys.stdout.buffer

    def send_msg(self, msg_type, ctxt=None, data=None):
        # TODO: minor code duplication with the method in DAPPServer, maybe refactor
        send_msg = {'msg_type': msg_type}
        if data:
            send_msg.update(data)
        msg = self._compose_msg(ctxt, data=send_msg)
        self.log(logging.DEBUG, 'Sending message to PingPong server:\n' + msg.decode('utf8'))
        self.write_fd.write(msg)
        self.write_fd.flush()

    def send_msg_failed(self, ctxt=None, fail_desc=''):
        """A shortcut to send "fail" message."""
        self.send_msg(msg_type='failed', ctxt=ctxt, data={'fail_desc': fail_desc})

    def send_msg_finished(self, ctxt=None, lres=False, res=''):
        """A shortcut to send "finished" message."""
        self.send_msg(msg_type='finished', ctxt=ctxt, data={'lres': lres, 'res':res})

    def recv_msg(self, allowed_types=None):
        lines = []
        line = ''
        while line != 'STOP':
            # strip just the trailing newline
            line = self.listen_fd.readline().decode('utf8')[:-1]
            lines.append(line)

        msg = self._msg_from_start_stop_list(lines)
        if msg is None:
            return None

        parsed_yaml = yaml.load(msg)
        self._check_loaded_msg(parsed_yaml, allowed_types)
        return parsed_yaml

    def pingpong(self):
        """A method that manages PingPong on client side;

        The flow:
        1) wait for DevAssistant to send a message of type "run"
        2) call the "run" method (this is supposed to be subclassed in the actual
           PingPong scripts)
        3) sends a message of type "finished" with result of the execution

        If an error occurs, a "fail" message with "fail_desc" is sent and sys.exit(1) is called.
        """
        # wait for "run" message
        try:
            msg = self.recv_msg(allowed_types=['run'])
        except DAPPException as e:
            self.send_msg_failed(ctxt=None, fail_desc=str(e))
            sys.exit(1)
        fail_desc = None
        if fail_desc is not None:
            self.send_msg_failed(ctxt, fail_desc)
            sys.exit(1)

        # actually run
        ctxt = msg.get('ctxt', {})
        try:
            run_result = self.run(ctxt)
        except BaseException as e:
            fail_desc = 'PingPong run method ended with an exception:\n{e}'.format(e=e)
            self.send_msg_failed(ctxt, fail_desc)
            sys.exit(1)

        if not isinstance(run_result, tuple) or len(run_result) != 2:
            fail_desc = ['PingPong run method ended with unexpected result:',
                str(run_result),
                '(expected 2-tuple)']
            self.send_msg_failed(ctxt, fail_desc)
            sys.exit(1)

        # send "finished" message to DevAssistant
        self.send_msg_finished(ctxt, lres=run_result[0], res=run_result[1])

    def call_command(self, command_type, command_input, ctxt):
        """Call a DevAssistant command.

        Args:
            command_type: DevAssistant command type
            command_input: command input for the called command
            ctxt: the global context

        Returns:
            2-tuple - logical result of command and result of command
            note, that ctxt argument gets modified if the command runner modifies it

        Raises:
            DAPPNoSuchCommand if there is no such command
        """
        self.send_msg(msg_type='call_command', ctxt=ctxt,
            data={'command_type': command_type, 'command_input': command_input})
        # if an exception is raised here, let it bubble up so that the calling method can
        #  deal with it as it wishes
        response = self.recv_msg(allowed_types=['command_result', 'no_such_command',
            'command_exception'])
        if response['msg_type'] == 'no_such_command':
            raise DAPPNoSuchCommand('No such DevAssistant command: "{ct}".'.\
                format(ct=command_type))
        elif response['msg_type'] == 'command_exception':
            raise DAPPCommandException('DevAssistant command raised exception:\n"{e}"'.\
                format(e=response.get('exception', 'No exception message.')))
        # we can't use ctxt.update(response['ctxt']), because the command might have
        #  also deleted some variables from the context
        update_ctxt(ctxt, response['ctxt'])
        return response['lres'], response['res']
