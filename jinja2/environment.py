# -*- coding: utf-8 -*-
"""
    jinja2.environment
    ~~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.lexer import Lexer
from jinja2.parser import Parser
from jinja2.optimizer import optimize
from jinja2.compiler import generate
from jinja2.defaults import DEFAULT_FILTERS, DEFAULT_TESTS, DEFAULT_NAMESPACE


class Environment(object):
    """The Jinja environment.

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
                 template_charset='utf-8',
                 loader=None):
        """Here the possible initialization parameters:

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
        `template_charset`        the charset of the templates.
        `loader`                  the loader which should be used.
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
        self.template_charset = template_charset

        # defaults
        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()

        # if no finalize function/method exists we default to unicode.  The
        # compiler check if the finalize attribute *is* unicode, if yes no
        # finalizaion is written where it can be avoided.
        if not hasattr(self, 'finalize'):
            self.finalize = unicode

        # set the loader provided
        self.loader = loader

        # create lexer
        self.lexer = Lexer(self)

    def parse(self, source, filename=None):
        """Parse the sourcecode and return the abstract syntax tree. This tree
        of nodes is used by the compiler to convert the template into
        executable source- or bytecode.
        """
        parser = Parser(self, source, filename)
        return parser.parse()

    def lex(self, source, filename=None):
        """Lex the given sourcecode and return a generator that yields tokens.
        The stream returned is not usable for Jinja but can be used if
        Jinja templates should be processed by other tools (for example
        syntax highlighting etc)

        The tuples are returned in the form ``(lineno, token, value)``.
        """
        return self.lexer.tokeniter(source, filename)

    def compile(self, source, filename=None, raw=False):
        """Compile a node or source."""
        if isinstance(source, basestring):
            source = self.parse(source, filename)
        node = optimize(source, self)
        source = generate(node, self)
        if raw:
            return source
        if isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        return compile(source, filename, 'exec')

    def join_path(self, template, parent):
        """Join a template with the parent.  By default all the lookups are
        relative to the loader root, but if the paths should be relative this
        function can be used to calculate the real filename."""
        return template

    def get_template(self, name, parent=None):
        """Load a template."""
        if self.loader is None:
            raise TypeError('no loader for this environment specified')
        if parent is not None:
            name = self.join_path(name, parent)
        return self.loader.load(self, name)


class Template(object):
    """Represents a template."""

    def __init__(self, environment, code):
        namespace = {'environment': environment}
        exec code in namespace
        self.environment = environment
        self.root_render_func = namespace['root']
        self.blocks = namespace['blocks']

    def render(self, *args, **kwargs):
        return u''.join(self.stream(*args, **kwargs))

    def stream(self, *args, **kwargs):
        context = dict(*args, **kwargs)
        return self.root_render_func(context)
