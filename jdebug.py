# -*- coding: utf-8 -*-
"""
    jdebug
    ~~~~~~

    Helper module to simplify jinja debugging. Use

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja import Environment
from jinja.parser import Parser
from jinja.lexer import Lexer
from jinja.translators.python import PythonTranslator


__all__ = ['e', 't', 'p', 'l']

e = Environment()
t = e.from_string

def p(x):
    print PythonTranslator(e, Parser(e, x).parse()).translate()

def l(x):
    for item in e.lexer.tokenize(x):
        print '%5s  %-20s  %r' % item
