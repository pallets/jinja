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
                 loader=None):
        """
        Here the possible initialization parameters:

        ========================= ============================================
        `block_start_string`      the string marking the begin of a block.
                                  this defaults to ``'{%'``.
        `block_end_string`        the string marking the end of a block.
                                  defaults to ``'%}'``.
        `variable_start_string`   the string marking the begin of a print
                                  statement. defaults to ``'{{'``.
        `comment_start_string`    the string marking the begin of a
                                  comment. defaults to ``'{#'``.
        `comment_end_string`      the string marking the end of a comment.
                                  defaults to ``'#}'``.
        `trim_blocks`             If this is set to ``True`` the first newline
                                  after a block is removed (block, not
                                  variable tag!). Defaults to ``False``.
        `loader`                  The loader for this environment.
        ========================= ============================================
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
        self.loader = loader

        # defaults
        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()

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
