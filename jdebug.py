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
import gc
from jinja import Environment
from jinja.parser import Parser
from jinja.lexer import Lexer
from jinja.translators.python import PythonTranslator


__all__ = ['e', 't', 'p', 'l', 'm']


_global_frame = sys._getframe()
e = Environment()
t = e.from_string


def p(x=None, f=None):
    if x is None and f is not None:
        x = e.loader.get_source(f)
    print PythonTranslator(e, Parser(e, x, f).parse(), None).translate()

def l(x):
    for token in e.lexer.tokenize(x):
        print '%5s  %-20s  %r' % (item.lineno,
                                  item.type,
                                  item.value)

class MemoryGuard(object):

    def __init__(self):
        self.guarded_objects = {}
        self.clear = self.guarded_objects.clear

    def freeze(self):
        self.clear()
        for obj in gc.get_objects():
            self.guarded_objects[id(obj)] = True

    def get_delta(self):
        frm = sys._getframe()
        result = []
        for obj in gc.get_objects():
            if id(obj) not in self.guarded_objects and \
               obj is not frm and obj is not result:
                result.append(obj)
        return result


m = MemoryGuard()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        from jinja import FileSystemLoader
        e.loader = FileSystemLoader(sys.argv[1])
    if len(sys.argv) > 2:
        p(f=sys.argv[2])
    else:
        p(sys.stdin.read())
