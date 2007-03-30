# -*- coding: utf-8 -*-
"""
    jdebug
    ~~~~~~

    Helper module to simplify jinja debugging. Use

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
from jinja import Environment
from jinja.parser import Parser
from jinja.lexer import Lexer
from jinja.translators.python import PythonTranslator


__all__ = ['e', 't', 'p', 'l']

e = Environment()
t = e.from_string


if os.environ.get('JDEBUG_SOURCEPRINT'):
    original_translate = PythonTranslator.translate

    def debug_translate(self):
        rv = original_translate(self)
        sys.stderr.write('## GENERATED SOURCE:\n%s\n' % rv)
        return rv

    PythonTranslator.translate = debug_translate


def p(x, f=None):
    print PythonTranslator(e, Parser(e, x, f).parse()).translate()

def l(x):
    for item in e.lexer.tokenize(x):
        print '%5s  %-20s  %r' % item
