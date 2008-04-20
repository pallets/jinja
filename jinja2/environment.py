# -*- coding: utf-8 -*-
"""
    jinja2.environment
    ~~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys
from jinja2.lexer import Lexer
from jinja2.parser import Parser
from jinja2.optimizer import optimize
from jinja2.compiler import generate
from jinja2.runtime import Undefined
from jinja2.debug import translate_exception
from jinja2.utils import import_string
from jinja2.defaults import DEFAULT_FILTERS, DEFAULT_TESTS, DEFAULT_NAMESPACE


class Environment(object):
    """The Jinja environment.

    The core component of Jinja is the `Environment`. It contains
    important shared variables like configuration, filters, tests,
    globals and others.
    """

    #: if this environment is sandboxed.  Modifying this variable won't make
    #: the environment sandboxed though.  For a real sandboxed environment
    #: have a look at jinja2.sandbox
    sandboxed = False

    def __init__(self,
                 block_start_string='{%',
                 block_end_string='%}',
                 variable_start_string='{{',
                 variable_end_string='}}',
                 comment_start_string='{#',
                 comment_end_string='#}',
                 line_statement_prefix=None,
                 trim_blocks=False,
                 optimized=True,
                 undefined=Undefined,
                 loader=None,
                 extensions=(),
                 finalize=unicode):
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
        `line_statement_prefix`   If given and a string, this will be used as
                                  prefix for line based statements.  See the
                                  documentation for more details.
        `trim_blocks`             If this is set to ``True`` the first newline
                                  after a block is removed (block, not
                                  variable tag!). Defaults to ``False``.
        `optimized`               should the optimizer be enabled?  Default is
                                  ``True``.
        `undefined`               a subclass of `Undefined` that is used to
                                  represent undefined variables.
        `loader`                  the loader which should be used.
        `extensions`              List of Jinja extensions to use.
        `finalize`                A callable that finalizes the variable.  Per
                                  default this is `unicode`, other useful
                                  builtin finalizers are `escape`.
        ========================= ============================================
        """

        # santity checks
        assert issubclass(undefined, Undefined), 'undefined must be ' \
               'a subclass of undefined because filters depend on it.'
        assert block_start_string != variable_start_string != \
               comment_start_string, 'block, variable and comment ' \
               'start strings must be different'

        # lexer / parser information
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string
        self.line_statement_prefix = line_statement_prefix
        self.trim_blocks = trim_blocks
        self.extensions = []
        for extension in extensions:
            if isinstance(extension, basestring):
                extension = import_string(extension)
            self.extensions.append(extension(self))

        # runtime information
        self.undefined = undefined
        self.optimized = optimized
        self.finalize = finalize

        # defaults
        self.filters = DEFAULT_FILTERS.copy()
        self.tests = DEFAULT_TESTS.copy()
        self.globals = DEFAULT_NAMESPACE.copy()
        for extension in self.extensions:
            extension.update_globals(self.globals)

        # set the loader provided
        self.loader = loader

        # create lexer
        self.lexer = Lexer(self)

    def subscribe(self, obj, argument):
        """Get an item or attribute of an object."""
        try:
            return getattr(obj, str(argument))
        except (AttributeError, UnicodeError):
            try:
                return obj[argument]
            except (TypeError, LookupError):
                return self.undefined(obj=obj, name=argument)

    def parse(self, source, name=None):
        """Parse the sourcecode and return the abstract syntax tree. This tree
        of nodes is used by the compiler to convert the template into
        executable source- or bytecode.
        """
        return Parser(self, source, name).parse()

    def lex(self, source, name=None):
        """Lex the given sourcecode and return a generator that yields tokens.
        The stream returned is not usable for Jinja but can be used if
        Jinja templates should be processed by other tools (for example
        syntax highlighting etc)

        The tuples are returned in the form ``(lineno, token, value)``.
        """
        return self.lexer.tokeniter(source, name)

    def compile(self, source, name=None, filename=None, globals=None,
                raw=False):
        """Compile a node or source.  The name is the load name of the
        template after it was joined using `join_path` if necessary,
        filename is the estimated filename of the template on the file
        system.  If the template came from a database or memory this
        can be omitted.
        """
        if isinstance(source, basestring):
            source = self.parse(source, name)
        if self.optimized:
            node = optimize(source, self, globals or {})
        source = generate(node, self, name, filename)
        if raw:
            return source
        if filename is None:
            filename = '<template>'
        elif isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        return compile(source, filename, 'exec')

    def join_path(self, template, parent):
        """Join a template with the parent.  By default all the lookups are
        relative to the loader root, but if the paths should be relative this
        function can be used to calculate the real filename."""
        return template

    def get_template(self, name, parent=None, globals=None):
        """Load a template."""
        if self.loader is None:
            raise TypeError('no loader for this environment specified')
        if parent is not None:
            name = self.join_path(name, parent)
        globals = self.make_globals(globals)
        return self.loader.load(self, name, globals)

    def from_string(self, source, globals=None):
        """Load a template from a string."""
        globals = self.make_globals(globals)
        return Template(self, self.compile(source, globals=globals),
                        globals)

    def make_globals(self, d):
        """Return a dict for the globals."""
        if d is None:
            return self.globals
        return dict(self.globals, **d)


class Template(object):
    """Represents a template."""

    def __init__(self, environment, code, globals, uptodate=None):
        namespace = {
            'environment':          environment,
            '__jinja_template__':   self
        }
        exec code in namespace
        self.environment = environment
        self.name = namespace['name']
        self.filename = code.co_filename
        self.root_render_func = namespace['root']
        self.blocks = namespace['blocks']
        self.globals = globals

        # debug and loader helpers
        self._get_debug_info = namespace['get_debug_info']
        self._uptodate = uptodate

    def render(self, *args, **kwargs):
        """Render the template into a string."""
        try:
            return u''.join(self.generate(*args, **kwargs))
        except:
            # hide the `generate` frame
            exc_type, exc_value, tb = sys.exc_info()
            raise exc_type, exc_value, tb.tb_next

    def stream(self, *args, **kwargs):
        """Return a `TemplateStream` that generates the template."""
        try:
            return TemplateStream(self.generate(*args, **kwargs))
        except:
            # hide the `generate` frame
            exc_type, exc_value, tb = sys.exc_info()
            raise exc_type, exc_value, tb.tb_next

    def generate(self, *args, **kwargs):
        """Return a generator that generates the template."""
        # assemble the context
        context = dict(*args, **kwargs)

        # if the environment is using the optimizer locals may never
        # override globals as optimizations might have happened
        # depending on values of certain globals.  This assertion goes
        # away if the python interpreter is started with -O
        if __debug__ and self.environment.optimized:
            overrides = set(context) & set(self.globals)
            if overrides:
                plural = len(overrides) != 1 and 's' or ''
                raise AssertionError('the per template variable%s %s '
                                     'override%s global variable%s. '
                                     'With an enabled optimizer this '
                                     'will lead to unexpected results.' %
                    (plural, ', '.join(overrides), plural or ' a', plural))
        gen = self.root_render_func(dict(self.globals, **context))
        # skip the first item which is a reference to the context
        gen.next()

        try:
            for event in gen:
                yield event
        except:
            exc_info = translate_exception(sys.exc_info())
            raise exc_info[0], exc_info[1], exc_info[2]

    def get_corresponding_lineno(self, lineno):
        """Return the source line number of a line number in the
        generated bytecode as they are not in sync.
        """
        for template_line, code_line in reversed(self._get_debug_info()):
            if code_line <= lineno:
                return template_line
        return 1

    @property
    def is_up_to_date(self):
        """Check if the template is still up to date."""
        if self._uptodate is None:
            return True
        return self._uptodate()

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.name
        )


class TemplateStream(object):
    """Wraps a genererator for outputing template streams."""

    def __init__(self, gen):
        self._gen = gen
        self._next = gen.next
        self.buffered = False

    def disable_buffering(self):
        """Disable the output buffering."""
        self._next = self._gen.next
        self.buffered = False

    def enable_buffering(self, size=5):
        """Enable buffering. Buffer `size` items before yielding them."""
        if size <= 1:
            raise ValueError('buffer size too small')
        self.buffered = True

        def buffering_next():
            buf = []
            c_size = 0
            push = buf.append
            next = self._gen.next

            try:
                while 1:
                    item = next()
                    if item:
                        push(item)
                        c_size += 1
                    if c_size >= size:
                        raise StopIteration()
            except StopIteration:
                if not c_size:
                    raise
            return u''.join(buf)

        self._next = buffering_next

    def __iter__(self):
        return self

    def next(self):
        return self._next()
