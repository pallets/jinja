# -*- coding: utf-8 -*-
"""
    jinja.environment
    ~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.lexer import Lexer
from jinja.parser import Parser
from jinja.loaders import LoaderWrapper
from jinja.datastructure import SilentUndefined, Markup, Context, FakeTranslator
from jinja.utils import collect_translations, get_attribute
from jinja.exceptions import FilterNotFound, TestNotFound, \
     SecurityException, TemplateSyntaxError
from jinja.defaults import DEFAULT_FILTERS, DEFAULT_TESTS, DEFAULT_NAMESPACE


__all__ = ['Environment']


#: minor speedup
_getattr = getattr


class Environment(object):
    """
    The Jinja environment.

    The core component of Jinja is the `Environment`. It contains
    important shared variables like configuration, filters, tests,
    globals and others.
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
                 undefined_singleton=SilentUndefined,
                 friendly_traceback=True,
                 translator_factory=None):
        """
        Here the possible initialization parameters:

        ========================= ============================================
        `block_start_string` *    the string marking the begin of a block.
                                  this defaults to ``'{%'``.
        `block_end_string` *      the string marking the end of a block.
                                  defaults to ``'%}'``.
        `variable_start_string` * the string marking the begin of a print
                                  statement. defaults to ``'{{'``.
        `comment_start_string` *  the string marking the begin of a
                                  comment. defaults to ``'{#'``.
        `comment_end_string` *    the string marking the end of a comment.
                                  defaults to ``'#}'``.
        `trim_blocks` *           If this is set to ``True`` the first newline
                                  after a block is removed (block, not
                                  variable tag!). Defaults to ``False``.
        `auto_escape`             If this is set to ``True`` Jinja will
                                  automatically escape all variables using xml
                                  escaping methods. If you don't want to
                                  escape a string you have to wrap it in a
                                  ``Markup`` object from the
                                  ``jinja.datastructure`` module. If
                                  `auto_escape` is ``True`` there will be also
                                  a ``Markup`` object in the template
                                  namespace to define partial html fragments.
                                  Note that we do not recomment this feature.
        `default_filters`         list of tuples in the form (``filter_name``,
                                  ``arguments``) where ``filter_name`` is the
                                  name of a registered filter and
                                  ``arguments`` a tuple with the filter
                                  arguments. The filters specified here will
                                  always be applied when printing data to the
                                  template. *new in Jinja 1.1*
        `template_charset`        The charset of the templates. Defaults
                                  to ``'utf-8'``.
        `charset`                 Charset of all string input data. Defaults
                                  to ``'utf-8'``.
        `namespace`               Global namespace for all templates.
        `loader`                  Specify a template loader.
        `filters`                 dict of filters or the default filters if
                                  not defined.
        `tests`                   dict of tests of the default tests if not
                                  defined.
        `context_class`           the context class this template should use.
                                  See the `Context` documentation for more
                                  details.
        `undefined_singleton`     The singleton value that is used for missing
                                  variables. *new in Jinja 1.1*
        `friendly_traceback`      Set this to `False` to disable the developer
                                  friendly traceback rewriting. Whenever an
                                  runtime or syntax error occours jinja will
                                  try to make a developer friendly traceback
                                  that shows the error in the template line.
                                  This however can be annoying when debugging
                                  broken functions that are called from the
                                  template. *new in Jinja 1.1*
        `translator_factory`      A callback function that is called with
                                  the context as first argument to get the
                                  translator for the current instance.
                                  *new in Jinja 1.2*
        ========================= ============================================

        All of these variables except those marked with a star (*) are
        modifiable after environment initialization.
        """

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
        if filters is None:
            filters = DEFAULT_FILTERS.copy()
        self.filters = filters
        if tests is None:
            tests = DEFAULT_TESTS.copy()
        self.tests = tests
        self.default_filters = default_filters or []
        self.context_class = context_class
        self.undefined_singleton = undefined_singleton
        self.friendly_traceback = friendly_traceback

        # global namespace
        if namespace is None:
            namespace = DEFAULT_NAMESPACE.copy()
        self.globals = namespace

        # jinja 1.0 compatibility
        if auto_escape:
            self.default_filters.append(('escape', (True,)))
            self.globals['Markup'] = Markup

        # and here the translator factory
        self.translator_factory = translator_factory

        # create lexer
        self.lexer = Lexer(self)

    def loader(self, value):
        """
        Get or set the template loader.
        """
        self._loader = LoaderWrapper(self, value)
    loader = property(lambda s: s._loader, loader, doc=loader.__doc__)

    def parse(self, source, filename=None):
        """
        Parse the sourcecode and return the abstract syntax tree. This tree
        of nodes is used by the `translators`_ to convert the template into
        executable source- or bytecode.

        .. _translators: translators.txt
        """
        parser = Parser(self, source, filename)
        return parser.parse()

    def lex(self, source, filename=None):
        """
        Lex the given sourcecode and return a generator that yields tokens.
        The stream returned is not usable for Jinja but can be used if
        Jinja templates should be processed by other tools (for example
        syntax highlighting etc)

        The tuples are returned in the form ``(lineno, token, value)``.
        """
        return self.lexer.tokeniter(source, filename)

    def from_string(self, source):
        """
        Load and parse a template source and translate it into eval-able
        Python code. This code is wrapped within a `Template` class that
        allows you to render it.
        """
        from jinja.translators.python import PythonTranslator
        try:
            rv = PythonTranslator.process(self, Parser(self, source).parse())
        except TemplateSyntaxError, e:
            # on syntax errors rewrite the traceback if wanted
            if not self.friendly_traceback:
                raise
            from jinja.debugger import raise_syntax_error
            __traceback_hide__ = True
            raise_syntax_error(e, self, source)
        else:
            # everything went well. attach the source and return it
            # the attached source is used by the traceback system for
            # debugging porposes
            rv._source = source
            return rv

    def get_template(self, filename):
        """
        Load a template from a loader. If the template does not exist, you
        will get a `TemplateNotFound` exception.
        """
        return self._loader.load(filename)

    def to_unicode(self, value):
        """
        Convert a value to unicode with the rules defined on the environment.
        """
        # undefined and None expand to ""
        if value in (None, self.undefined_singleton):
            return u''
        # things that are already unicode can pass. As long as nobody
        # does ugly things with the class it works for jinja too
        elif isinstance(value, unicode):
            return value
        # otherwise try to use __unicode__ or decode __str__
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
        if self.translator_factory is not None:
            return self.translator_factory(context)
        return FakeTranslator()

    def get_translations(self, name):
        """
        Load template `name` and return all translatable strings (note that
        that it really just returns the strings form this template, not from
        the parent or any included templates!)
        """
        return collect_translations(self.loader.parse(name))

    def get_translations_for_string(self, string):
        """
        Like `get_translations`, but the translations are loaded from a
        normal string that represents the template.
        """
        return collect_translations(self.parse(string))

    def apply_filters(self, value, context, filters):
        """
        Apply a list of filters on the variable.
        """
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

        cache = context.cache
        for key in filters:
            if key in cache:
                func = cache[key]
            else:
                filtername, args = key
                if filtername not in self.filters:
                    raise FilterNotFound(filtername)
                cache[key] = func = self.filters[filtername](*args)
            value = func(self, context, value)
        return value

    def perform_test(self, context, testname, args, value, invert):
        """
        Perform a test on a variable.
        """
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

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
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

        try:
            return obj[name]
        except (TypeError, KeyError, IndexError, AttributeError):
            try:
                return get_attribute(obj, name)
            except (AttributeError, SecurityException):
                pass
        if obj is self.undefined_singleton:
            return _getattr(obj, name)
        return self.undefined_singleton

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
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

        if dyn_args is not None:
            args += tuple(dyn_args)
        if dyn_kwargs is not None:
            kwargs.update(dyn_kwargs)
        if _getattr(f, 'jinja_unsafe_call', False) or \
           _getattr(f, 'alters_data', False):
            return self.undefined_singleton
        if _getattr(f, 'jinja_context_callable', False):
            args = (self, context) + args
        return f(*args, **kwargs)

    def call_function_simple(self, f, context):
        """
        Function call without arguments. Because of the smaller signature and
        fewer logic here we have a bit of redundant code.
        """
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

        if _getattr(f, 'jinja_unsafe_call', False) or \
           _getattr(f, 'alters_data', False):
            return self.undefined_singleton
        if _getattr(f, 'jinja_context_callable', False):
            return f(self, context)
        return f()

    def finish_var(self, value, ctx):
        """
        As long as no write_var function is passed to the template
        evaluator the source generated by the python translator will
        call this function for all variables.
        """
        # some traceback systems allow to skip frames. but allow
        # disabling that via -O to not make things slow
        if __debug__:
            __traceback_hide__ = True

        if value is None:
            return u''
        elif value is self.undefined_singleton:
            return unicode(value)
        elif _getattr(value, 'jinja_no_finalization', False):
            return value
        val = self.to_unicode(value)
        if self.default_filters:
            val = self.apply_filters(val, ctx, self.default_filters)
        return val
