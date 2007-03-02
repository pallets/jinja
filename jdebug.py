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
from jinja.translators.python import PythonTranslator


__all__ = ['e', 't', 'p']

e = Environment()
t = e.from_string

def p(x):
    print PythonTranslator(e, Parser(e, x).parse()).translate()
