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
from jinja.datastructure import Undefined, Markup, Context, FakeTranslator
from jinja.utils import escape, collect_translations, get_attribute
from jinja.exceptions import FilterNotFound, TestNotFound, \
     SecurityException, TemplateSyntaxError, TemplateRuntimeError
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
                 default_filters=None,
                 template_charset='utf-8',
                 charset='utf-8',
                 namespace=None,
                 loader=None,
                 filters=None,
                 tests=None,
                 context_class=Context,
                 silent=True,
                 friendly_traceback=True):

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
        self.default_filters = default_filters or []
        self.context_class = context_class
        self.silent = silent
        self.friendly_traceback = friendly_traceback

        # global namespace
        self.globals = namespace is None and DEFAULT_NAMESPACE.copy() \
                       or namespace

        # jinja 1.0 compatibility
        if auto_escape:
            self.default_filters.append(('escape', (True,)))
            self.globals['Markup'] = Markup

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
        try:
            rv = PythonTranslator.process(self, Parser(self, source).parse())
        except TemplateSyntaxError, e:
            # on syntax errors rewrite the traceback if wanted
            if not self.friendly_traceback:
                raise
            from jinja.utils import raise_syntax_error
            __traceback_hide__ = True
            raise_syntax_error(e, self, source)
        else:
            # everything went well. attach the source and return it
            # attach the source for debugging
            rv._source = source
            return rv

    def get_template(self, filename):
        """Load a template from a filename. Only works
        if a proper loader is set."""
        return self._loader.load(filename)

    def to_unicode(self, value):
        """
        Convert a value to unicode with the rules defined on the environment.
        """
        if value in (None, Undefined):
            return u''
        elif isinstance(value, unicode):
            return value
        else:
            try:
                return unicode(value)
            except UnicodeError:
                return str(value).decode(self.charset, 'ignore')

    def get_translator(self, context):
        """
        Return the translator for i18n.

        A translator is an object that provides the two functions
        ``gettext(string)`` and ``ngettext(singular, plural, n)``. Note
        that both of them have to return unicode!
        """
        return FakeTranslator()

    def get_translations(self, name):
        """
        Load template `name` and return all translatable strings (note that
        that it really just returns the strings form this template, not from
        the parent or any included templates!)
        """
        return collect_translations(self.loader.parse(name))

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
        Get one attribute from an object.
        """
        try:
            return obj[name]
        except (TypeError, KeyError, IndexError):
            try:
                return get_attribute(obj, name)
            except (AttributeError, SecurityException):
                pass
        if self.silent:
            return Undefined
        raise TemplateRuntimeError('attribute %r or object %r not defined' % (
            name, obj))

    def get_attributes(self, obj, attributes):
        """
        Get some attributes from an object. If attributes is an
        empty sequence the object is returned as it.
        """
        get = self.get_attribute
        for name in attributes:
            obj = get(obj, name)
        return obj

    def call_function(self, f, context, args, kwargs, dyn_args, dyn_kwargs):
        """
        Function call helper. Called for all functions that are passed
        any arguments.
        """
        if dyn_args is not None:
            args += tuple(dyn_args)
        elif dyn_kwargs is not None:
            kwargs.update(dyn_kwargs)
        if getattr(f, 'jinja_unsafe_call', False) or \
           getattr(f, 'alters_data', False):
            return Undefined
        if getattr(f, 'jinja_context_callable', False):
            args = (self, context) + args
        return f(*args, **kwargs)

    def call_function_simple(self, f, context):
        """
        Function call without arguments. Because of the smaller signature and
        fewer logic here we have a bit of redundant code.
        """
        if getattr(f, 'jinja_unsafe_call', False) or \
           getattr(f, 'alters_data', False):
            return Undefined
        if getattr(f, 'jinja_context_callable', False):
            return f(self, context)
        return f()

    def finish_var(self, value, ctx):
        """
        As long as no write_var function is passed to the template
        evaluator the source generated by the python translator will
        call this function for all variables.
        """
        if value is Undefined or value is None:
            return u''
        val = self.to_unicode(value)
        if self.default_filters:
            val = self.apply_filters(val, ctx, self.default_filters)
        return val
