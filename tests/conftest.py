# -*- coding: utf-8 -*-
"""
    conftest
    ~~~~~~~~

    Configure py.test for support stuff.

    :copyright: 2007 by Armin Ronacher, Alexander Schremmer.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import py
from jinja import Environment
from jinja.parser import Parser


class GlobalLoader(object):

    def __init__(self, scope):
        self.scope = scope

    def get_source(self, environment, name, parent, scope=None):
        return self.scope[name.upper() + 'TEMPLATE']

    def parse(self, environment, name, parent, scope=None):
        return Parser(environment, self.get_source(environment, name,
                      parent, scope), name).parse()

    def load(self, environment, name, translator, scope=None):
        return translator.process(environment, self.parse(environment,
                                  name, None, scope))


loader = GlobalLoader(globals())
simple_env = Environment(trim_blocks=True, loader=loader)


class Module(py.test.collect.Module):

    def __init__(self, *args, **kwargs):
        self.env = simple_env
        super(Module, self).__init__(*args, **kwargs)

    def join(self, name):
        obj = getattr(self.obj, name)
        if hasattr(obj, 'func_code'):
            return JinjaTestFunction(name, parent=self)


class JinjaTestFunction(py.test.collect.Function):

    def execute(self, target, *args):
        loader.scope = target.func_globals
        co = target.func_code
        if 'env' in co.co_varnames[:co.co_argcount]:
            target(self.parent.env, *args)
        else:
            target(*args)
