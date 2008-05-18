# -*- coding: utf-8 -*-
"""
    jinja2.compiler
    ~~~~~~~~~~~~~~~

    Compiles nodes into python code.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
from time import time
from copy import copy
from random import randrange
from keyword import iskeyword
from cStringIO import StringIO
from itertools import chain
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.exceptions import TemplateAssertionError
from jinja2.utils import Markup, concat


operators = {
    'eq':       '==',
    'ne':       '!=',
    'gt':       '>',
    'gteq':     '>=',
    'lt':       '<',
    'lteq':     '<=',
    'in':       'in',
    'notin':    'not in'
}

try:
    exec '(0 if 0 else 0)'
except SyntaxError:
    have_condexpr = False
else:
    have_condexpr = True


def generate(node, environment, name, filename, stream=None):
    """Generate the python source for a node tree."""
    if not isinstance(node, nodes.Template):
        raise TypeError('Can\'t compile non template nodes')
    node.freeze()
    generator = CodeGenerator(environment, name, filename, stream)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


def has_safe_repr(value):
    """Does the node have a safe representation?"""
    if value is None or value is NotImplemented or value is Ellipsis:
        return True
    if isinstance(value, (bool, int, long, float, complex, basestring,
                          xrange, Markup)):
        return True
    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            if not has_safe_repr(item):
                return False
        return True
    elif isinstance(value, dict):
        for key, value in value.iteritems():
            if not has_safe_repr(key):
                return False
            if not has_safe_repr(value):
                return False
        return True
    return False


def find_undeclared(nodes, names):
    """Check if the names passed are accessed undeclared.  The return value
    is a set of all the undeclared names from the sequence of names found.
    """
    visitor = UndeclaredNameVisitor(names)
    try:
        for node in nodes:
            visitor.visit(node)
    except VisitorExit:
        pass
    return visitor.undeclared


class Identifiers(object):
    """Tracks the status of identifiers in frames."""

    def __init__(self):
        # variables that are known to be declared (probably from outer
        # frames or because they are special for the frame)
        self.declared = set()

        # undeclared variables from outer scopes
        self.outer_undeclared = set()

        # names that are accessed without being explicitly declared by
        # this one or any of the outer scopes.  Names can appear both in
        # declared and undeclared.
        self.undeclared = set()

        # names that are declared locally
        self.declared_locally = set()

        # names that are declared by parameters
        self.declared_parameter = set()

    def add_special(self, name):
        """Register a special name like `loop`."""
        self.undeclared.discard(name)
        self.declared.add(name)

    def is_declared(self, name, local_only=False):
        """Check if a name is declared in this or an outer scope."""
        if name in self.declared_locally or name in self.declared_parameter:
            return True
        if local_only:
            return False
        return name in self.declared

    def find_shadowed(self):
        """Find all the shadowed names."""
        return (self.declared | self.outer_undeclared) & \
               (self.declared_locally | self.declared_parameter)


class Frame(object):
    """Holds compile time information for us."""

    def __init__(self, parent=None):
        self.identifiers = Identifiers()

        # a toplevel frame is the root + soft frames such as if conditions.
        self.toplevel = False

        # the root frame is basically just the outermost frame, so no if
        # conditions.  This information is used to optimize inheritance
        # situations.
        self.rootlevel = False

        # inside some tags we are using a buffer rather than yield statements.
        # this for example affects {% filter %} or {% macro %}.  If a frame
        # is buffered this variable points to the name of the list used as
        # buffer.
        self.buffer = None

        # the name of the block we're in, otherwise None.
        self.block = parent and parent.block or None

        # the parent of this frame
        self.parent = parent

        if parent is not None:
            self.identifiers.declared.update(
                parent.identifiers.declared |
                parent.identifiers.declared_locally |
                parent.identifiers.declared_parameter |
                parent.identifiers.undeclared
            )
            self.identifiers.outer_undeclared.update(
                parent.identifiers.undeclared -
                self.identifiers.declared
            )
            self.buffer = parent.buffer

    def copy(self):
        """Create a copy of the current one."""
        rv = copy(self)
        rv.identifiers = copy(self.identifiers)
        return rv

    def inspect(self, nodes, hard_scope=False):
        """Walk the node and check for identifiers.  If the scope is hard (eg:
        enforce on a python level) overrides from outer scopes are tracked
        differently.
        """
        visitor = FrameIdentifierVisitor(self.identifiers, hard_scope)
        for node in nodes:
            visitor.visit(node)

    def inner(self):
        """Return an inner frame."""
        return Frame(self)

    def soft(self):
        """Return a soft frame.  A soft frame may not be modified as
        standalone thing as it shares the resources with the frame it
        was created of, but it's not a rootlevel frame any longer.
        """
        rv = copy(self)
        rv.rootlevel = False
        return rv


class VisitorExit(RuntimeError):
    """Exception used by the `UndeclaredNameVisitor` to signal a stop."""


class DependencyFinderVisitor(NodeVisitor):
    """A visitor that collects filter and test calls."""

    def __init__(self):
        self.filters = set()
        self.tests = set()

    def visit_Filter(self, node):
        self.generic_visit(node)
        self.filters.add(node.name)

    def visit_Test(self, node):
        self.generic_visit(node)
        self.tests.add(node.name)

    def visit_Block(self, node):
        """Stop visiting at blocks."""


class UndeclaredNameVisitor(NodeVisitor):
    """A visitor that checks if a name is accessed without being
    declared.  This is different from the frame visitor as it will
    not stop at closure frames.
    """

    def __init__(self, names):
        self.names = set(names)
        self.undeclared = set()

    def visit_Name(self, node):
        if node.ctx == 'load' and node.name in self.names:
            self.undeclared.add(node.name)
            if self.undeclared == self.names:
                raise VisitorExit()
        else:
            self.names.discard(node.name)

    def visit_Block(self, node):
        """Stop visiting a blocks."""


class FrameIdentifierVisitor(NodeVisitor):
    """A visitor for `Frame.inspect`."""

    def __init__(self, identifiers, hard_scope):
        self.identifiers = identifiers
        self.hard_scope = hard_scope

    def visit_Name(self, node):
        """All assignments to names go through this function."""
        if node.ctx == 'store':
            self.identifiers.declared_locally.add(node.name)
        elif node.ctx == 'param':
            self.identifiers.declared_parameter.add(node.name)
        elif node.ctx == 'load' and not \
             self.identifiers.is_declared(node.name, self.hard_scope):
            self.identifiers.undeclared.add(node.name)

    def visit_Macro(self, node):
        self.identifiers.declared_locally.add(node.name)

    def visit_Import(self, node):
        self.generic_visit(node)
        self.identifiers.declared_locally.add(node.target)

    def visit_FromImport(self, node):
        self.generic_visit(node)
        for name in node.names:
            if isinstance(name, tuple):
                self.identifiers.declared_locally.add(name[1])
            else:
                self.identifiers.declared_locally.add(name)

    def visit_Assign(self, node):
        """Visit assignments in the correct order."""
        self.visit(node.node)
        self.visit(node.target)

    def visit_For(self, node):
        """Visiting stops at for blocks.  However the block sequence
        is visited as part of the outer scope.
        """
        self.visit(node.iter)

    def visit_CallBlock(self, node):
        for child in node.iter_child_nodes(exclude=('body',)):
            self.visit(child)

    def visit_FilterBlock(self, node):
        self.visit(node.filter)

    def visit_Block(self, node):
        """Stop visiting at blocks."""


class CompilerExit(Exception):
    """Raised if the compiler encountered a situation where it just
    doesn't make sense to further process the code.  Any block that
    raises such an exception is not further processed.
    """


class CodeGenerator(NodeVisitor):

    def __init__(self, environment, name, filename, stream=None):
        if stream is None:
            stream = StringIO()
        self.environment = environment
        self.name = name
        self.filename = filename
        self.stream = stream

        # aliases for imports
        self.import_aliases = {}

        # a registry for all blocks.  Because blocks are moved out
        # into the global python scope they are registered here
        self.blocks = {}

        # the number of extends statements so far
        self.extends_so_far = 0

        # some templates have a rootlevel extends.  In this case we
        # can safely assume that we're a child template and do some
        # more optimizations.
        self.has_known_extends = False

        # the current line number
        self.code_lineno = 1

        # registry of all filters and tests (global, not block local)
        self.tests = {}
        self.filters = {}

        # the debug information
        self.debug_info = []
        self._write_debug_info = None

        # the number of new lines before the next write()
        self._new_lines = 0

        # the line number of the last written statement
        self._last_line = 0

        # true if nothing was written so far.
        self._first_write = True

        # used by the `temporary_identifier` method to get new
        # unique, temporary identifier
        self._last_identifier = 0

        # the current indentation
        self._indentation = 0

    def temporary_identifier(self):
        """Get a new unique identifier."""
        self._last_identifier += 1
        return 't%d' % self._last_identifier

    def buffer(self, frame):
        """Enable buffering for the frame from that point onwards."""
        frame.buffer = buf = self.temporary_identifier()
        self.writeline('%s = []' % buf)
        return buf

    def return_buffer_contents(self, frame):
        """Return the buffer contents of the frame."""
        if self.environment.autoescape:
            self.writeline('return Markup(concat(%s))' % frame.buffer)
        else:
            self.writeline('return concat(%s)' % frame.buffer)

    def indent(self):
        """Indent by one."""
        self._indentation += 1

    def outdent(self, step=1):
        """Outdent by step."""
        self._indentation -= step

    def blockvisit(self, nodes, frame, force_generator=True):
        """Visit a list of nodes as block in a frame.  If the current frame
        is no buffer a dummy ``if 0: yield None`` is written automatically
        unless the force_generator parameter is set to False.
        """
        if frame.buffer is None and force_generator:
            self.writeline('if 0: yield None')
        try:
            for node in nodes:
                self.visit(node, frame)
        except CompilerExit:
            pass

    def write(self, x):
        """Write a string into the output stream."""
        if self._new_lines:
            if not self._first_write:
                self.stream.write('\n' * self._new_lines)
                self.code_lineno += self._new_lines
                if self._write_debug_info is not None:
                    self.debug_info.append((self._write_debug_info,
                                            self.code_lineno))
                    self._write_debug_info = None
            self._first_write = False
            self.stream.write('    ' * self._indentation)
            self._new_lines = 0
        self.stream.write(x)

    def writeline(self, x, node=None, extra=0):
        """Combination of newline and write."""
        self.newline(node, extra)
        self.write(x)

    def newline(self, node=None, extra=0):
        """Add one or more newlines before the next write."""
        self._new_lines = max(self._new_lines, 1 + extra)
        if node is not None and node.lineno != self._last_line:
            self._write_debug_info = node.lineno
            self._last_line = node.lineno

    def signature(self, node, frame, have_comma=True, extra_kwargs=None):
        """Writes a function call to the stream for the current node.
        Per default it will write a leading comma but this can be
        disabled by setting have_comma to False.  The extra keyword
        arguments may not include python keywords otherwise a syntax
        error could occour.  The extra keyword arguments should be given
        as python dict.
        """
        have_comma = have_comma and [True] or []
        def touch_comma():
            if have_comma:
                self.write(', ')
            else:
                have_comma.append(True)

        # if any of the given keyword arguments is a python keyword
        # we have to make sure that no invalid call is created.
        kwarg_workaround = False
        for kwarg in chain((x.key for x in node.kwargs), extra_kwargs or ()):
            if iskeyword(kwarg):
                kwarg_workaround = True
                break

        for arg in node.args:
            touch_comma()
            self.visit(arg, frame)

        if not kwarg_workaround:
            for kwarg in node.kwargs:
                touch_comma()
                self.visit(kwarg, frame)
            if extra_kwargs is not None:
                for key, value in extra_kwargs.iteritems():
                    touch_comma()
                    self.write('%s=%s' % (key, value))
        if node.dyn_args:
            touch_comma()
            self.write('*')
            self.visit(node.dyn_args, frame)

        if kwarg_workaround:
            touch_comma()
            if node.dyn_kwargs is not None:
                self.write('**dict({')
            else:
                self.write('**{')
            for kwarg in node.kwargs:
                self.write('%r: ' % kwarg.key)
                self.visit(kwarg.value, frame)
                self.write(', ')
            if extra_kwargs is not None:
                for key, value in extra_kwargs.iteritems():
                    self.write('%r: %s, ' % (key, value))
            if node.dyn_kwargs is not None:
                self.write('}, **')
                self.visit(node.dyn_kwargs, frame)
                self.write(')')
            else:
                self.write('}')

        elif node.dyn_kwargs is not None:
            touch_comma()
            self.write('**')
            self.visit(node.dyn_kwargs, frame)

    def pull_locals(self, frame):
        """Pull all the references identifiers into the local scope."""
        for name in frame.identifiers.undeclared:
            self.writeline('l_%s = context.resolve(%r)' % (name, name))

    def pull_dependencies(self, nodes):
        """Pull all the dependencies."""
        visitor = DependencyFinderVisitor()
        for node in nodes:
            visitor.visit(node)
        for dependency in 'filters', 'tests':
            mapping = getattr(self, dependency)
            for name in getattr(visitor, dependency):
                if name not in mapping:
                    mapping[name] = self.temporary_identifier()
                self.writeline('%s = environment.%s[%r]' %
                               (mapping[name], dependency, name))

    def collect_shadowed(self, frame):
        """This function returns all the shadowed variables in a dict
        in the form name: alias and will write the required assignments
        into the current scope.  No indentation takes place.
        """
        aliases = {}
        for name in frame.identifiers.find_shadowed():
            aliases[name] = ident = self.temporary_identifier()
            self.writeline('%s = l_%s' % (ident, name))
        return aliases

    def function_scoping(self, node, frame, children=None,
                         find_special=True):
        """In Jinja a few statements require the help of anonymous
        functions.  Those are currently macros and call blocks and in
        the future also recursive loops.  As there is currently
        technical limitation that doesn't allow reading and writing a
        variable in a scope where the initial value is coming from an
        outer scope, this function tries to fall back with a common
        error message.  Additionally the frame passed is modified so
        that the argumetns are collected and callers are looked up.

        This will return the modified frame.
        """
        # we have to iterate twice over it, make sure that works
        if children is None:
            children = node.iter_child_nodes()
        children = list(children)
        func_frame = frame.inner()
        func_frame.inspect(children, hard_scope=True)

        # variables that are undeclared (accessed before declaration) and
        # declared locally *and* part of an outside scope raise a template
        # assertion error. Reason: we can't generate reasonable code from
        # it without aliasing all the variables.  XXX: alias them ^^
        overriden_closure_vars = (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared &
            (func_frame.identifiers.declared_locally |
             func_frame.identifiers.declared_parameter)
        )
        if overriden_closure_vars:
            vars = ', '.join(sorted(overriden_closure_vars))
            raise TemplateAssertionError('It\'s not possible to set and '
                                         'access variables derived from '
                                         'an outer scope! (affects: %s' %
                                         vars, node.lineno, self.name,
                                         self.filename)

        # remove variables from a closure from the frame's undeclared
        # identifiers.
        func_frame.identifiers.undeclared -= (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared
        )

        # no special variables for this scope, abort early
        if not find_special:
            return func_frame

        func_frame.accesses_kwargs = False
        func_frame.accesses_varargs = False
        func_frame.accesses_caller = False
        func_frame.arguments = args = ['l_' + x.name for x in node.args]

        undeclared = find_undeclared(children, ('caller', 'kwargs', 'varargs'))

        if 'caller' in undeclared:
            func_frame.accesses_caller = True
            func_frame.identifiers.add_special('caller')
            args.append('l_caller')
        if 'kwargs' in undeclared:
            func_frame.accesses_kwargs = True
            func_frame.identifiers.add_special('kwargs')
            args.append('l_kwargs')
        if 'varargs' in undeclared:
            func_frame.accesses_varargs = True
            func_frame.identifiers.add_special('varargs')
            args.append('l_varargs')
        return func_frame

    # -- Visitors

    def visit_Template(self, node, frame=None):
        assert frame is None, 'no root frame allowed'
        from jinja2.runtime import __all__ as exported
        self.writeline('from __future__ import division')
        self.writeline('from jinja2.runtime import ' + ', '.join(exported))

        # do we have an extends tag at all?  If not, we can save some
        # overhead by just not processing any inheritance code.
        have_extends = node.find(nodes.Extends) is not None

        # find all blocks
        for block in node.find_all(nodes.Block):
            if block.name in self.blocks:
                raise TemplateAssertionError('block %r defined twice' %
                                             block.name, block.lineno,
                                             self.name, self.filename)
            self.blocks[block.name] = block

        # find all imports and import them
        for import_ in node.find_all(nodes.ImportedName):
            if import_.importname not in self.import_aliases:
                imp = import_.importname
                self.import_aliases[imp] = alias = self.temporary_identifier()
                if '.' in imp:
                    module, obj = imp.rsplit('.', 1)
                    self.writeline('from %s import %s as %s' %
                                   (module, obj, alias))
                else:
                    self.writeline('import %s as %s' % (imp, alias))

        # add the load name
        self.writeline('name = %r' % self.name)

        # generate the root render function.
        self.writeline('def root(context, environment=environment):', extra=1)

        # process the root
        frame = Frame()
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True
        self.indent()
        if have_extends:
            self.writeline('parent_template = None')
        self.pull_locals(frame)
        self.pull_dependencies(node.body)
        if 'self' in find_undeclared(node.body, ('self',)):
            frame.identifiers.add_special('self')
            self.writeline('l_self = TemplateReference(context)')
        self.blockvisit(node.body, frame)
        self.outdent()

        # make sure that the parent root is called.
        if have_extends:
            if not self.has_known_extends:
                self.indent()
                self.writeline('if parent_template is not None:')
            self.indent()
            self.writeline('for event in parent_template.'
                           'root_render_func(context):')
            self.indent()
            self.writeline('yield event')
            self.outdent(2 + (not self.has_known_extends))

        # at this point we now have the blocks collected and can visit them too.
        for name, block in self.blocks.iteritems():
            block_frame = Frame()
            block_frame.inspect(block.body)
            block_frame.block = name
            self.writeline('def block_%s(context, environment=environment):'
                           % name, block, 1)
            self.indent()
            undeclared = find_undeclared(block.body, ('self', 'super'))
            if 'self' in undeclared:
                block_frame.identifiers.add_special('self')
                self.writeline('l_self = TemplateReference(context)')
            if 'super' in undeclared:
                block_frame.identifiers.add_special('super')
                self.writeline('l_super = context.super(%r, '
                               'block_%s)' % (name, name))
            self.pull_locals(block_frame)
            self.pull_dependencies(block.body)
            self.blockvisit(block.body, block_frame)
            self.outdent()

        self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
                                                   for x in self.blocks),
                       extra=1)

        # add a function that returns the debug info
        self.writeline('debug_info = %r' % '&'.join('%s=%s' % x for x
                                                    in self.debug_info))

    def visit_Block(self, node, frame):
        """Call a block and register it for the template."""
        level = 1
        if frame.toplevel:
            # if we know that we are a child template, there is no need to
            # check if we are one
            if self.has_known_extends:
                return
            if self.extends_so_far > 0:
                self.writeline('if parent_template is None:')
                self.indent()
                level += 1
        self.writeline('for event in context.blocks[%r][0](context):' %
                       node.name, node)
        self.indent()
        if frame.buffer is None:
            self.writeline('yield event')
        else:
            self.writeline('%s.append(event)' % frame.buffer)
        self.outdent(level)

    def visit_Extends(self, node, frame):
        """Calls the extender."""
        if not frame.toplevel:
            raise TemplateAssertionError('cannot use extend from a non '
                                         'top-level scope', node.lineno,
                                         self.name, self.filename)

        # if the number of extends statements in general is zero so
        # far, we don't have to add a check if something extended
        # the template before this one.
        if self.extends_so_far > 0:

            # if we have a known extends we just add a template runtime
            # error into the generated code.  We could catch that at compile
            # time too, but i welcome it not to confuse users by throwing the
            # same error at different times just "because we can".
            if not self.has_known_extends:
                self.writeline('if parent_template is not None:')
                self.indent()
            self.writeline('raise TemplateRuntimeError(%r)' %
                           'extended multiple times')

            # if we have a known extends already we don't need that code here
            # as we know that the template execution will end here.
            if self.has_known_extends:
                raise CompilerExit()
            self.outdent()

        self.writeline('parent_template = environment.get_template(', node)
        self.visit(node.template, frame)
        self.write(', %r)' % self.name)
        self.writeline('for name, parent_block in parent_template.'
                       'blocks.iteritems():')
        self.indent()
        self.writeline('context.blocks.setdefault(name, []).'
                       'append(parent_block)')
        self.outdent()

        # if this extends statement was in the root level we can take
        # advantage of that information and simplify the generated code
        # in the top level from this point onwards
        if frame.rootlevel:
            self.has_known_extends = True

        # and now we have one more
        self.extends_so_far += 1

    def visit_Include(self, node, frame):
        """Handles includes."""
        if node.with_context:
            self.writeline('template = environment.get_template(', node)
            self.visit(node.template, frame)
            self.write(', %r)' % self.name)
            self.writeline('for event in template.root_render_func('
                           'template.new_context(context.parent, True)):')
        else:
            self.writeline('for event in environment.get_template(', node)
            self.visit(node.template, frame)
            self.write(', %r).module._TemplateModule__body_stream:' %
                       self.name)
        self.indent()
        if frame.buffer is None:
            self.writeline('yield event')
        else:
            self.writeline('%s(event)' % frame.buffer)
        self.outdent()

    def visit_Import(self, node, frame):
        """Visit regular imports."""
        self.writeline('l_%s = ' % node.target, node)
        if frame.toplevel:
            self.write('context.vars[%r] = ' % node.target)
        self.write('environment.get_template(')
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module(context.parent, True)')
        else:
            self.write('module')
        if frame.toplevel and not node.target.startswith('__'):
            self.writeline('context.exported_vars.discard(%r)' % node.target)

    def visit_FromImport(self, node, frame):
        """Visit named imports."""
        self.newline(node)
        self.write('included_template = environment.get_template(')
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module(context.parent, True)')
        else:
            self.write('module')

        var_names = []
        discarded_names = []
        for name in node.names:
            if isinstance(name, tuple):
                name, alias = name
            else:
                alias = name
            self.writeline('l_%s = getattr(included_template, '
                           '%r, missing)' % (alias, name))
            self.writeline('if l_%s is missing:' % alias)
            self.indent()
            self.writeline('l_%s = environment.undefined(%r %% '
                           'included_template.__name__, '
                           'name=%r)' %
                           (alias, 'the template %r does not export '
                            'the requested name ' + repr(name), name))
            self.outdent()
            if frame.toplevel:
                var_names.append(alias)
                if not alias.startswith('__'):
                    discarded_names.append(alias)

        if var_names:
            if len(var_names) == 1:
                name = var_names[0]
                self.writeline('context.vars[%r] = l_%s' % (name, name))
            else:
                self.writeline('context.vars.update({%s})' % ', '.join(
                    '%r: l_%s' % (name, name) for name in var_names
                ))
        if discarded_names:
            if len(discarded_names) == 1:
                self.writeline('context.exported_vars.discard(%r)' %
                               discarded_names[0])
            else:
                self.writeline('context.exported_vars.difference_'
                               'update((%s))' % ', '.join(map(repr, discarded_names)))

    def visit_For(self, node, frame):
        # when calculating the nodes for the inner frame we have to exclude
        # the iterator contents from it
        children = node.iter_child_nodes(exclude=('iter',))

        if node.recursive:
            loop_frame = self.function_scoping(node, frame, children,
                                               find_special=False)
        else:
            loop_frame = frame.inner()
            loop_frame.inspect(children)

        extended_loop = node.recursive or node.else_ or \
                        'loop' in loop_frame.identifiers.undeclared
        if extended_loop:
            loop_frame.identifiers.add_special('loop')

        # if we don't have an recursive loop we have to find the shadowed
        # variables at that point
        if not node.recursive:
            aliases = self.collect_shadowed(loop_frame)

        # otherwise we set up a buffer and add a function def
        else:
            self.writeline('def loop(reciter, loop_render_func):', node)
            self.indent()
            self.buffer(loop_frame)
            aliases = {}

        self.pull_locals(loop_frame)
        if node.else_:
            self.writeline('l_loop = None')

        self.newline(node)
        self.writeline('for ')
        self.visit(node.target, loop_frame)
        self.write(extended_loop and ', l_loop in LoopContext(' or ' in ')

        # the expression pointing to the parent loop.  We make the
        # undefined a bit more debug friendly at the same time.
        parent_loop = 'loop' in aliases and aliases['loop'] \
                      or "environment.undefined(%r, name='loop')" % "'loop' " \
                         'is undefined. "the filter section of a loop as well ' \
                         'as the else block doesn\'t have access to the ' \
                         "special 'loop' variable of the current loop.  " \
                         "Because there is no parent loop it's undefined."

        # if we have an extened loop and a node test, we filter in the
        # "outer frame".
        if extended_loop and node.test is not None:
            self.write('(')
            self.visit(node.target, loop_frame)
            self.write(' for ')
            self.visit(node.target, loop_frame)
            self.write(' in ')
            if node.recursive:
                self.write('reciter')
            else:
                self.visit(node.iter, loop_frame)
            self.write(' if (')
            test_frame = loop_frame.copy()
            self.writeline('l_loop = ' + parent_loop)
            self.visit(node.test, test_frame)
            self.write('))')

        elif node.recursive:
            self.write('reciter')
        else:
            self.visit(node.iter, loop_frame)

        if node.recursive:
            self.write(', recurse=loop_render_func):')
        else:
            self.write(extended_loop and '):' or ':')

        # tests in not extended loops become a continue
        if not extended_loop and node.test is not None:
            self.indent()
            self.writeline('if not ')
            self.visit(node.test, loop_frame)
            self.write(':')
            self.indent()
            self.writeline('continue')
            self.outdent(2)

        self.indent()
        self.blockvisit(node.body, loop_frame, force_generator=True)
        self.outdent()

        if node.else_:
            self.writeline('if l_loop is None:')
            self.indent()
            self.writeline('l_loop = ' + parent_loop)
            self.blockvisit(node.else_, loop_frame, force_generator=False)
            self.outdent()

        # reset the aliases if there are any.
        for name, alias in aliases.iteritems():
            self.writeline('l_%s = %s' % (name, alias))

        # if the node was recursive we have to return the buffer contents
        # and start the iteration code
        if node.recursive:
            self.return_buffer_contents(loop_frame)
            self.outdent()
            if frame.buffer is None:
                self.writeline('yield loop(', node)
            else:
                self.writeline('%s.append(loop(' % frame.buffer, node)
            self.visit(node.iter, frame)
            self.write(', loop)')
            if frame.buffer is not None:
                self.write(')')

    def visit_If(self, node, frame):
        if_frame = frame.soft()
        self.writeline('if ', node)
        self.visit(node.test, if_frame)
        self.write(':')
        self.indent()
        self.blockvisit(node.body, if_frame)
        self.outdent()
        if node.else_:
            self.writeline('else:')
            self.indent()
            self.blockvisit(node.else_, if_frame)
            self.outdent()

    def visit_Macro(self, node, frame):
        macro_frame = self.function_scoping(node, frame)
        args = macro_frame.arguments
        self.writeline('def macro(%s):' % ', '.join(args), node)
        self.indent()
        self.buffer(macro_frame)
        self.pull_locals(macro_frame)
        self.blockvisit(node.body, macro_frame)
        self.return_buffer_contents(macro_frame)
        self.outdent()
        self.newline()
        if frame.toplevel:
            if not node.name.startswith('__'):
                self.write('context.exported_vars.add(%r)' % node.name)
            self.writeline('context.vars[%r] = ' % node.name)
        arg_tuple = ', '.join(repr(x.name) for x in node.args)
        if len(node.args) == 1:
            arg_tuple += ','
        self.write('l_%s = Macro(environment, macro, %r, (%s), (' %
                   (node.name, node.name, arg_tuple))
        for arg in node.defaults:
            self.visit(arg, macro_frame)
            self.write(', ')
        self.write('), %s, %s, %s)' % (
            macro_frame.accesses_kwargs and '1' or '0',
            macro_frame.accesses_varargs and '1' or '0',
            macro_frame.accesses_caller and '1' or '0'
        ))

    def visit_CallBlock(self, node, frame):
        call_frame = self.function_scoping(node, frame, node.iter_child_nodes
                                           (exclude=('call',)))
        args = call_frame.arguments
        self.writeline('def call(%s):' % ', '.join(args), node)
        self.indent()
        self.pull_locals(call_frame)
        self.buffer(call_frame)
        self.blockvisit(node.body, call_frame)
        self.return_buffer_contents(call_frame)
        self.outdent()
        arg_tuple = ', '.join(repr(x.name) for x in node.args)
        if len(node.args) == 1:
            arg_tuple += ','
        self.writeline('caller = Macro(environment, call, None, (%s), (' %
                       arg_tuple)
        for arg in node.defaults:
            self.visit(arg, call_frame)
            self.write(', ')
        self.write('), %s, %s, 0)' % (
            call_frame.accesses_kwargs and '1' or '0',
            call_frame.accesses_varargs and '1' or '0'
        ))
        if frame.buffer is None:
            self.writeline('yield ', node)
        else:
            self.writeline('%s.append(' % frame.buffer, node)
        self.visit_Call(node.call, call_frame,
                        extra_kwargs={'caller': 'caller'})
        if frame.buffer is not None:
            self.write(')')

    def visit_FilterBlock(self, node, frame):
        filter_frame = frame.inner()
        filter_frame.inspect(node.iter_child_nodes())

        aliases = self.collect_shadowed(filter_frame)
        self.pull_locals(filter_frame)
        self.buffer(filter_frame)

        for child in node.body:
            self.visit(child, filter_frame)

        if frame.buffer is None:
            self.writeline('yield ', node)
        else:
            self.writeline('%s.append(' % frame.buffer, node)
        self.visit_Filter(node.filter, filter_frame, 'concat(%s)'
                          % filter_frame.buffer)
        if frame.buffer is not None:
            self.write(')')

    def visit_ExprStmt(self, node, frame):
        self.newline(node)
        self.visit(node.node, frame)

    def visit_Output(self, node, frame):
        # if we have a known extends statement, we don't output anything
        if self.has_known_extends and frame.toplevel:
            return

        self.newline(node)

        # if we are in the toplevel scope and there was already an extends
        # statement we have to add a check that disables our yield(s) here
        # so that they don't appear in the output.
        outdent_later = False
        if frame.toplevel and self.extends_so_far != 0:
            self.writeline('if parent_template is None:')
            self.indent()
            outdent_later = True

        # try to evaluate as many chunks as possible into a static
        # string at compile time.
        body = []
        for child in node.nodes:
            try:
                const = unicode(child.as_const())
            except:
                body.append(child)
                continue
            if body and isinstance(body[-1], list):
                body[-1].append(const)
            else:
                body.append([const])

        # if we have less than 3 nodes or a buffer we yield or extend/append
        if len(body) < 3 or frame.buffer is not None:
            if frame.buffer is not None:
                # for one item we append, for more we extend
                if len(body) == 1:
                    self.writeline('%s.append(' % frame.buffer)
                else:
                    self.writeline('%s.extend((' % frame.buffer)
                self.indent()
            for item in body:
                if isinstance(item, list):
                    val = repr(concat(item))
                    if frame.buffer is None:
                        self.writeline('yield ' + val)
                    else:
                        self.writeline(val + ', ')
                else:
                    if frame.buffer is None:
                        self.writeline('yield ', item)
                    else:
                        self.newline(item)
                    close = 1
                    if self.environment.autoescape:
                        self.write('escape(')
                    else:
                        self.write('unicode(')
                    if self.environment.finalize is not None:
                        self.write('environment.finalize(')
                        close += 1
                    self.visit(item, frame)
                    self.write(')' * close)
                    if frame.buffer is not None:
                        self.write(', ')
            if frame.buffer is not None:
                # close the open parentheses
                self.outdent()
                self.writeline(len(body) == 1 and ')' or '))')

        # otherwise we create a format string as this is faster in that case
        else:
            format = []
            arguments = []
            for item in body:
                if isinstance(item, list):
                    format.append(concat(item).replace('%', '%%'))
                else:
                    format.append('%s')
                    arguments.append(item)
            self.writeline('yield ')
            self.write(repr(concat(format)) + ' % (')
            idx = -1
            self.indent()
            for argument in arguments:
                self.newline(argument)
                close = 0
                if self.environment.autoescape:
                    self.write('escape(')
                    close += 1
                if self.environment.finalize is not None:
                    self.write('environment.finalize(')
                    close += 1
                self.visit(argument, frame)
                self.write(')' * close + ', ')
            self.outdent()
            self.writeline(')')

        if outdent_later:
            self.outdent()

    def visit_Assign(self, node, frame):
        self.newline(node)
        # toplevel assignments however go into the local namespace and
        # the current template's context.  We create a copy of the frame
        # here and add a set so that the Name visitor can add the assigned
        # names here.
        if frame.toplevel:
            assignment_frame = frame.copy()
            assignment_frame.assigned_names = set()
        else:
            assignment_frame = frame
        self.visit(node.target, assignment_frame)
        self.write(' = ')
        self.visit(node.node, frame)

        # make sure toplevel assignments are added to the context.
        if frame.toplevel:
            public_names = [x for x in assignment_frame.assigned_names
                            if not x.startswith('__')]
            if len(assignment_frame.assigned_names) == 1:
                name = iter(assignment_frame.assigned_names).next()
                self.writeline('context.vars[%r] = l_%s' % (name, name))
            else:
                self.writeline('context.vars.update({')
                for idx, name in enumerate(assignment_frame.assigned_names):
                    if idx:
                        self.write(', ')
                    self.write('%r: l_%s' % (name, name))
                self.write('})')
            if public_names:
                if len(public_names) == 1:
                    self.writeline('context.exported_vars.add(%r)' %
                                   public_names[0])
                else:
                    self.writeline('context.exported_vars.update((%s))' %
                                   ', '.join(map(repr, public_names)))

    def visit_Name(self, node, frame):
        if node.ctx == 'store' and frame.toplevel:
            frame.assigned_names.add(node.name)
        self.write('l_' + node.name)

    def visit_Const(self, node, frame):
        val = node.value
        if isinstance(val, float):
            self.write(str(val))
        else:
            self.write(repr(val))

    def visit_Tuple(self, node, frame):
        self.write('(')
        idx = -1
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(idx == 0 and ',)' or ')')

    def visit_List(self, node, frame):
        self.write('[')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(']')

    def visit_Dict(self, node, frame):
        self.write('{')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item.key, frame)
            self.write(': ')
            self.visit(item.value, frame)
        self.write('}')

    def binop(operator):
        def visitor(self, node, frame):
            self.write('(')
            self.visit(node.left, frame)
            self.write(' %s ' % operator)
            self.visit(node.right, frame)
            self.write(')')
        return visitor

    def uaop(operator):
        def visitor(self, node, frame):
            self.write('(' + operator)
            self.visit(node.node, frame)
            self.write(')')
        return visitor

    visit_Add = binop('+')
    visit_Sub = binop('-')
    visit_Mul = binop('*')
    visit_Div = binop('/')
    visit_FloorDiv = binop('//')
    visit_Pow = binop('**')
    visit_Mod = binop('%')
    visit_And = binop('and')
    visit_Or = binop('or')
    visit_Pos = uaop('+')
    visit_Neg = uaop('-')
    visit_Not = uaop('not ')
    del binop, uaop

    def visit_Concat(self, node, frame):
        self.write('%s((' % (self.environment.autoescape and
                             'markup_join' or 'unicode_join'))
        for arg in node.nodes:
            self.visit(arg, frame)
            self.write(', ')
        self.write('))')

    def visit_Compare(self, node, frame):
        self.visit(node.expr, frame)
        for op in node.ops:
            self.visit(op, frame)

    def visit_Operand(self, node, frame):
        self.write(' %s ' % operators[node.op])
        self.visit(node.expr, frame)

    def visit_Subscript(self, node, frame):
        # slices or integer subscriptions bypass the subscribe
        # method if we can determine that at compile time.
        if isinstance(node.arg, nodes.Slice) or \
           (isinstance(node.arg, nodes.Const) and
            isinstance(node.arg.value, (int, long))):
            self.visit(node.node, frame)
            self.write('[')
            self.visit(node.arg, frame)
            self.write(']')
            return
        self.write('environment.subscribe(')
        self.visit(node.node, frame)
        self.write(', ')
        self.visit(node.arg, frame)
        self.write(')')

    def visit_Slice(self, node, frame):
        if node.start is not None:
            self.visit(node.start, frame)
        self.write(':')
        if node.stop is not None:
            self.visit(node.stop, frame)
        if node.step is not None:
            self.write(':')
            self.visit(node.step, frame)

    def visit_Filter(self, node, frame, initial=None):
        self.write(self.filters[node.name] + '(')
        func = self.environment.filters.get(node.name)
        if func is None:
            raise TemplateAssertionError('no filter named %r' % node.name,
                                         node.lineno, self.name,
                                         self.filename)
        if getattr(func, 'contextfilter', False):
            self.write('context, ')
        elif getattr(func, 'environmentfilter', False):
            self.write('environment, ')
        if isinstance(node.node, nodes.Filter):
            self.visit_Filter(node.node, frame, initial)
        elif node.node is None:
            self.write(initial)
        else:
            self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    def visit_Test(self, node, frame):
        self.write(self.tests[node.name] + '(')
        if node.name not in self.environment.tests:
            raise TemplateAssertionError('no test named %r' % node.name,
                                         node.lineno, self.name,
                                         self.filename)
        self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    def visit_CondExpr(self, node, frame):
        if not have_condexpr:
            self.write('((')
            self.visit(node.test, frame)
            self.write(') and (')
            self.visit(node.expr1, frame)
            self.write(',) or (')
            self.visit(node.expr2, frame)
            self.write(',))[0]')
        else:
            self.write('(')
            self.visit(node.expr1, frame)
            self.write(' if ')
            self.visit(node.test, frame)
            self.write(' else ')
            self.visit(node.expr2, frame)
            self.write(')')

    def visit_Call(self, node, frame, extra_kwargs=None):
        if self.environment.sandboxed:
            self.write('environment.call(')
        self.visit(node.node, frame)
        self.write(self.environment.sandboxed and ', ' or '(')
        self.signature(node, frame, False, extra_kwargs)
        self.write(')')

    def visit_Keyword(self, node, frame):
        self.write(node.key + '=')
        self.visit(node.value, frame)

    # Unused nodes for extensions

    def visit_MarkSafe(self, node, frame):
        self.write('Markup(')
        self.visit(node.expr, frame)
        self.write(')')

    def visit_EnvironmentAttribute(self, node, frame):
        self.write('environment.' + node.name)

    def visit_ExtensionAttribute(self, node, frame):
        self.write('environment.extensions[%r].%s' % (node.identifier, node.attr))

    def visit_ImportedName(self, node, frame):
        self.write(self.import_aliases[node.importname])

    def visit_InternalName(self, node, frame):
        self.write(node.name)

    def visit_Continue(self, node, frame):
        self.writeline('continue', node)

    def visit_Break(self, node, frame):
        self.writeline('break', node)
