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
from jinja2 import Environment
from jinja2.loaders import BaseLoader
from jinja2.exceptions import TemplateNotFound

try:
    # This code adds support for coverage.py (see
    # http://nedbatchelder.com/code/modules/coverage.html).
    # It prints a coverage report for the modules specified in all
    # module globals (of the test modules) named "coverage_modules".

    import coverage, atexit

    IGNORED_MODULES = ['jinja2._speedups', 'jinja2.defaults',
                       'jinja2.translators']

    def report_coverage():
        coverage.stop()
        module_list = [
            mod for name, mod in sys.modules.copy().iteritems() if
            getattr(mod, '__file__', None) and
            name.startswith('jinja2.') and
            name not in IGNORED_MODULES
        ]
        module_list.sort()
        coverage.report(module_list)

    def callback(option, opt_str, value, parser):
        atexit.register(report_coverage)
        coverage.erase()
        coverage.start()

    py.test.config.addoptions('Test options', py.test.config.Option('-C',
        '--coverage', action='callback', callback=callback,
        help='Output information about code coverage (slow!)'))

except ImportError:
    coverage = None


class GlobalLoader(BaseLoader):
    scope = globals()

    def get_source(self, environment, name):
        try:
            return self.scope[name.upper() + 'TEMPLATE'], None, None
        except KeyError:
            raise TemplateNotFound(name)


loader = GlobalLoader()
simple_env = Environment(trim_blocks=True, loader=loader, cache_size=0)


class Module(py.test.collect.Module):

    def __init__(self, *args, **kwargs):
        self.env = simple_env
        super(Module, self).__init__(*args, **kwargs)

    def makeitem(self, name, obj, usefilters=True):
        if name.startswith('test_'):
            if hasattr(obj, 'func_code'):
                return JinjaTestFunction(name, parent=self)
            elif isinstance(obj, basestring):
                return JinjaDocTest(name, parent=self)


class JinjaTestFunction(py.test.collect.Function):

    def execute(self, target, *args):
        loader.scope = target.func_globals
        co = target.func_code
        if 'env' in co.co_varnames[:co.co_argcount]:
            target(self.parent.env, *args)
        else:
            target(*args)


class JinjaDocTest(py.test.collect.Item):

    def run(self):
        mod = py.std.types.ModuleType(self.name)
        mod.__doc__ = self.obj
        self.execute(mod)

    def execute(self, mod):
        mod.env = self.parent.env
        mod.MODULE = self.parent.obj
        failed, tot = py.compat.doctest.testmod(mod, verbose=True)
        if failed:
            py.test.fail('doctest %s: %s failed out of %s' % (
                         self.fspath, failed, tot))
