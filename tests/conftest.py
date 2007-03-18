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
from inspect import isclass
from jinja import Environment


simple_env = Environment(trim_blocks=True)


class Module(py.test.collect.Module):

    def __init__(self, *args, **kwargs):
        self.env = simple_env
        super(Module, self).__init__(*args, **kwargs)

    def join(self, name):
        obj = getattr(self.obj, name)
        if isclass(obj):
            return JinjaClassCollector(name, parent=self)
        elif hasattr(obj, 'func_code'):
            return JinjaTestFunction(name, parent=self)


class JinjaTestFunction(py.test.collect.Function):

    def execute(self, target, *args):
        co = target.func_code
        if 'env' in co.co_varnames[:co.co_argcount]:
            target(self.parent.env, *args)
        else:
            target(*args)


class JinjaClassCollector(py.test.collect.Class):

    Function = JinjaTestFunction

    def setup(self):
        cls = self.obj
        cls.env = self.parent.env
        super(JinjaClassCollector, self).setup()
