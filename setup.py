#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import subprocess

try:
    from setuptools import setup, find_packages, Command
except:
    from distutils.core import setup, find_packages, Command

import dapp

class PyTest(Command):
    # this is cut'n'pasted from DevAssistant setup.py; we should refactor it in
    #  a simple standalone library
    user_options = [('test-runner=',
                     't',
                     'test runner to use; by default, multiple py.test runners are tried')]
    command_consumes_arguments = True

    def initialize_options(self):
        self.test_runner = None
        self.args = []

    def finalize_options(self):
        pass

    def runner_exists(self, runner):
        syspaths = os.getenv('PATH').split(os.pathsep)
        for p in syspaths:
            if os.path.exists(os.path.join(p, runner)):
                return True

        return False

    def run(self):
        # if user provides a runner and it's not found, this fails
        #  otherwise it first tries various versioned runners and if it doesn't
        #  find any, it tries "py.test" - if that's not found either, this fails
        supported = ['2.6', '2.7', '3.3', '3.4']
        potential_runners = ['py.test-' + s for s in supported]
        if self.test_runner:
            potential_runners = [self.test_runner]
        runners = [pr for pr in potential_runners if self.runner_exists(pr)]

        if len(runners) == 0:
            if not self.test_runner and self.runner_exists('py.test'):
                runners = ['py.test']
            else:
                print('No py.test runners found, can\'t run tests.', file=sys.stderr)
                print('Tried: {0}.'.format(', '.join(runners + ['py.test'])), file=sys.stderr)
                raise SystemExit(100)

        for runner in runners:
            if len(runners) > 1:
                print('\n' * 2)
            print('Running tests using "{0}":'.format(runner))

            retcode = 0
            cmd = [runner]
            for a in self.args:
                cmd.append(a)
            cmd.append('test')
            t = subprocess.Popen(cmd)
            rc = t.wait()
            retcode = t.returncode or retcode

        raise SystemExit(retcode)


setup(
    name='dapp',
    version=dapp.__version__,
    description='Library implementing DevAssistant PingPong protocol',
    long_description=''.join(open('README.rst').readlines()),
    keywords='devassistant,pipe,protocol,pingpong',
    author='Bohuslav "Slavek" Kabrda',
    author_email='bkabrda@redhat.com',
    license='GPLv2+',
    packages=find_packages(exclude=['test']),
    install_requires=['PyYAML'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        ],
    cmdclass={'test': PyTest},
)
