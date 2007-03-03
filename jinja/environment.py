# -*- coding: utf-8 -*-
"""
    jinja.environment
    ~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja.lexer import Lexer
from jinja.parser import Parser
from jinja.loaders import LoaderWrapper
from jinja.datastructure import Undefined
from jinja.utils import escape
from jinja.exceptions import FilterNotFound, TestNotFound, SecurityException
from jinja.defaults import DEFAULT_FILTERS, DEFAULT_TESTS, DEFAULT_NAMESPACE


class Environment(object):
    """
    The jinja environment.
    """

    def __init__(self,
                 block_start_string='{%',
                 block_end_string='%}',
                 variable_start_string='{{',
                 variable_end_string='}}',
                 comment_start_string='{#',
                 comment_end_string='#}',
                 trim_blocks=False,
                 auto_escape=False,
                 template_charset='utf-8',
                 charset='utf-8',
                 namespace=None,
                 loader=None,
                 filters=None,
                 tests=None):

        # lexer / parser information
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string
        self.trim_blocks = trim_blocks

        # other stuff
        self.template_charset = template_charset
        self.charset = charset
        self.loader = loader
        self.filters = filters is None and DEFAULT_FILTERS.copy() or filters
        self.tests = tests is None and DEFAULT_TESTS.copy() or tests
        self.auto_escape = auto_escape

        # global namespace
        self.globals = namespace is None and DEFAULT_NAMESPACE.copy() \
                       or namespace

        # create lexer
        self.lexer = Lexer(self)

    def loader(self, value):
        """
        Get or set the template loader.
        """
        self._loader = LoaderWrapper(self, value)
    loader = property(lambda s: s._loader, loader, loader.__doc__)

    def parse(self, source, filename=None):
        """Function that creates a new parser and parses the source."""
        parser = Parser(self, source, filename)
        return parser.parse()

    def from_string(self, source):
        """Load a template from a string."""
        from jinja.parser import Parser
        from jinja.translators.python import PythonTranslator
        return PythonTranslator.process(self, Parser(self, source).parse())

    def get_template(self, filename):
        """Load a template from a filename. Only works
        if a proper loader is set."""
        return self._loader.load(filename)

    def to_unicode(self, value):
        """
        Convert a value to unicode with the rules defined on the environment.
        """
        if isinstance(value, unicode):
            return value
        else:
            try:
                return unicode(value)
            except UnicodeError:
                return str(value).decode(self.charset, 'ignore')

    def apply_filters(self, value, context, filters):
        """
        Apply a list of filters on the variable.
        """
        for key in filters:
            if key in context.cache:
                func = context.cache[key]
            else:
                filtername, args = key
                if filtername not in self.filters:
                    raise FilterNotFound(filtername)
                context.cache[key] = func = self.filters[filtername](*args)
            value = func(self, context, value)
        return value

    def perform_test(self, context, testname, args, value, invert):
        """
        Perform a test on a variable.
        """
        key = (testname, args)
        if key in context.cache:
            func = context.cache[key]
        else:
            if testname not in self.tests:
                raise TestNotFound(testname)
            context.cache[key] = func = self.tests[testname](*args)
        rv = func(self, context, value)
        if invert:
            return not rv
        return bool(rv)

    def get_attribute(self, obj, name):
        """
        Get the attribute name from obj.
        """
        if name in obj:
            return obj[name]
        elif hasattr(obj, name):
            rv = getattr(obj, name)
            r = getattr(obj, 'jinja_allowed_attributes', None)
            if r is not None:
                if name not in r:
                    raise SecurityException('unsafe attributed %r accessed' % name)
            return rv
        return Undefined

    def call_function(self, f, args, kwargs, dyn_args, dyn_kwargs):
        """
        Function call helper. Called for all functions that are passed
        any arguments.
        """
        if dyn_args is not None:
            args += tuple(dyn_args)
        elif dyn_kwargs is not None:
            kwargs.update(dyn_kwargs)
        if getattr(f, 'jinja_unsafe_call', False):
            raise SecurityException('unsafe function %r called' % f.__name__)
        return f(*args, **kwargs)

    def call_function_simple(self, f):
        """
        Function call without arguments.
        """
        if getattr(f, 'jinja_unsafe_call', False):
            raise SecurityException('unsafe function %r called' % f.__name__)
        return f()

    def finish_var(self, value):
        """
        As long as no write_var function is passed to the template
        evaluator the source generated by the python translator will
        call this function for all variables.
        """
        if value is Undefined:
            return u''
        elif self.auto_escape:
            return escape(value, True)
        return unicode(value)
