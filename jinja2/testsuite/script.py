# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.script
    ~~~~~~~~~~~~~~~~~~~~~~~

    All the unittests regarding the command line script.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import __main__ as script
from jinja2.testsuite import JinjaTestCase, here

from glob import glob
from os.path import join, isfile
from subprocess import Popen, PIPE
from sys import executable, version_info
import unittest


parse_test_cases = [
    {
        'eval': False,
        'in': [],
        'out': {},
    },
    {
        'eval': False,
        'in': ['x=1', 'y=2'],
        'out': {'x': '1', 'y': '2'},
    },
    {
        'eval': True,
        'in': ['x=1'],
        'out': {'x': 1},
    },
    {
        'eval': False,
        'in': ['x=1=2'],
        'out': {'x': '1=2'},
    },
]


def slurp(filename):
    with open(filename) as fo:
        return fo.read()


class ScriptTestCase(JinjaTestCase):

    def test_parse_cmdline_vars(self):
        for case in parse_test_cases:
            out = script.parse_cmdline_vars(case['in'], case['eval'])
            expected = case['out']
            assert out == expected, '{in} failed [eval={eval}]'.format(**case)

    def load_args(self, argsfile):
        if not isfile(argsfile):
            return {}

        with open(argsfile) as fo:
            return [line.strip() for line in fo]

    def iter_cases(self):
        # Cases are split to 3 files: .in, .out and .args (JSON)
        cases_dir = join(here, 'res', 'script')
        for infile in glob(join(cases_dir, '*.in')):
            argsfile = infile.replace('.in', '.args')
            case = {
                'args': self.load_args(argsfile),
                'in': slurp(infile),
            }

            outfile = infile.replace('.in', '.out')
            assert isfile(outfile), 'no output file for {}'.format(infile)
            case['out'] = slurp(outfile)

            yield case

    def run_script(self, data, args):
        '''Run a script with args, return output and return code'''
        if version_info[:2] > (2, 6):
            module = 'jinja2'
        else:
            module = 'jinja2.__main__'

        cmd = [executable, '-m{0}'.format(module)] + args
        pipe = Popen(cmd, stdin=PIPE, stdout=PIPE)
        pipe.stdin.write(data.encode('UTF-8'))
        pipe.stdin.close()
        out = pipe.stdout.read().decode('UTF-8')

        return out, pipe.wait()

    def test_script(self):
        for case in self.iter_cases():
            expected = case['out'].strip()
            out, rval = self.run_script(case['in'], case['args'])
            assert rval == 0, 'script failed'
            assert out.strip() == expected, 'bad output'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ScriptTestCase))
    return suite
