DevAssistant PingPong
=====================

Library implementing protocol used for communication between DevAssistant and PingPong
scripts (a.k.a. executable assistants). The protocol specification can be found at TODO:link.

Note that this library implements both "server" and "client" side. The "server" side
is only used by DevAssistant itself. If you're considering implementing a DevAssistant
PingPong library for another language, you just need to implement the "client" side.

Usage
-----

To write a simple PingPong script, you need to create a minimal Yaml assistant,
that specifies metadata, dependencies needed to run the PingPong script (which
is a Python 3 script in this case)::

  fullname: PingPong script example
  description: A simple PingPong script using DevAssistant PingPong protocol

  dependencies:
  # TODO: once dapp library is on PyPI/packaged in Fedora, it should also be added to list of deps
  - rpm: [python3]

  args:
    name:
      flags: [-n, --name]
      help: Please provide your name.

  files:
    script: &script
      source: script.py

  run:
  - pingpong: python3 *script

Let's assume that the above assistant is ``~/.devassistant/assistants/crt/test.yaml``. The
corresponding PingPong script has to be ``~/.devassistant/files/crt/test/script.py``
and can look like this::

  #!/usr/bin/python3
  import dapp

  class MyScript(dapp.DAPPClient):
      def run(self, ctxt):
          if 'name' in ctxt:
              name = ctxt['name'].capitalize()
          else:
              name = 'Stranger'
          self.call_command('log_i', 'Hello {n}!'.format(n=name), ctxt)
          return (True, 'I greeted him!')

  if __name__ == '__main__':
      MyScript().pingpong()

Things to Note
--------------

- The PingPong script class has to subclass ``dapp.DAPPClient``.
- The ``run`` method has to accept two arguments, ``self`` (Python specific argument pointing to
  the object) and ``ctxt``. The ``ctxt`` is a dict (Python mapping type) that holds the global context
  of the Yaml DSL (e.g. it contains the ``name`` argument, if it was specified by user on command
  line/in GUI).
- You can utilize DevAssistant commands [1] by calling ``call_command`` method. This takes three
  arguments - *command type*, *command input* and global context. The first two are the same as
  explained at [1], the third is (possibly modified) context that was passed to the ``run`` method.
- The ``ctxt`` dict can possibly get modified by running the command, check documentation of every
  specific command to see what it does and whether it modifies anything in the global context.
- The ``call_command`` method returns a 2-tuple - *logical result* and *result* of the command.
  Again, these are documented for all commands at [1].
- The ``run`` method has to return a 2-tuple - a *logical result* (e.g. ``True/False``) and a
  *result*, just as any other command would.
- If you want the assistant to modify the global context, just modify the ``ctxt`` variable.
  All commands that you possibly run after ``pingpong`` in the Yaml file will then see all
  the modifications that you did.
- Note, that to actually start the PingPong script, you have to call ``pingpong()`` method
  of the script class, **not** the ``run()`` method.


[1] http://docs.devassistant.org/en/latest/developer_documentation/command_reference.html
