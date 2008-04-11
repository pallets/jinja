# -*- coding: utf-8 -*-
"""
    jinja2.compiler
    ~~~~~~~~~~~~~~~

    Compiles nodes into python code.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
from copy import copy
from random import randrange
from cStringIO import StringIO
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.exceptions import TemplateAssertionError
from jinja2.runtime import StaticLoopContext


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


def generate(node, environment, filename, stream=None):
    """Generate the python source for a node tree."""
    is_child = node.find(nodes.Extends) is not None
    generator = CodeGenerator(environment, is_child, filename, stream)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


def has_safe_repr(value):
    """Does the node have a safe representation?"""
    if value is None or value is NotImplemented or value is Ellipsis:
        return True
    if isinstance(value, (bool, int, long, float, complex, basestring,
                          StaticLoopContext)):
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


class Identifiers(object):
    """Tracks the status of identifiers in frames."""

    def __init__(self):
        # variables that are known to be declared (probably from outer
        # frames or because they are special for the frame)
        self.declared = set()

        # names that are accessed without being explicitly declared by
        # this one or any of the outer scopes.  Names can appear both in
        # declared and undeclared.
        self.undeclared = set()

        # names that are declared locally
        self.declared_locally = set()

        # names that are declared by parameters
        self.declared_parameter = set()

        # filters that are declared locally
        self.declared_filter = set()
        self.undeclared_filter = dict()

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
        return self.declared & (self.declared_locally | self.declared_parameter)


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
        self.parent = parent
        self.block = parent and parent.block or None
        if parent is not None:
            self.identifiers.declared.update(
                parent.identifiers.declared |
                parent.identifiers.declared_locally |
                parent.identifiers.declared_parameter
            )

    def copy(self):
        """Create a copy of the current one."""
        rv = copy(self)
        rv.identifiers = copy(self)
        return rv

    def inspect(self, nodes, hard_scope=False):
        """Walk the node and check for identifiers.  If the scope
        is hard (eg: enforce on a python level) overrides from outer
        scopes are tracked differently.
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


class FrameIdentifierVisitor(NodeVisitor):
    """A visitor for `Frame.inspect`."""

    def __init__(self, identifiers, hard_scope):
        self.identifiers = identifiers
        self.hard_scope = hard_scope

    def visit_Name(self, node):
        """All assignments to names go through this function."""
        if node.ctx in ('store', 'param'):
            self.identifiers.declared_locally.add(node.name)
        elif node.ctx == 'load':
            if not self.identifiers.is_declared(node.name, self.hard_scope):
                self.identifiers.undeclared.add(node.name)

    def visit_Filter(self, node):
        if not node.name in self.identifiers.declared_filter:
            uf = self.identifiers.undeclared_filter.get(node.name, 0) + 1
            if uf > 1:
                self.identifiers.declared_filter.add(node.name)
            self.identifiers.undeclared_filter[node.name] = uf

    def visit_Macro(self, node):
        """Macros set local."""
        self.identifiers.declared_locally.add(node.name)

    def visit_Assign(self, node):
        """Visit assignments in the correct order."""
        self.visit(node.node)
        self.visit(node.target)

    # stop traversing at instructions that have their own scope.
    visit_Block = visit_CallBlock = visit_FilterBlock = \
        visit_For = lambda s, n: None


class CompilerExit(Exception):
    """Raised if the compiler encountered a situation where it just
    doesn't make sense to further process the code.  Any block that
    raises such an exception is not further processed."""


class CodeGenerator(NodeVisitor):

    def __init__(self, environment, is_child, filename, stream=None):
        if stream is None:
            stream = StringIO()
        self.environment = environment
        self.is_child = is_child
        self.filename = filename
        self.stream = stream
        self.blocks = {}
        self.indentation = 0
        self.new_lines = 0
        self.last_identifier = 0
        self.extends_so_far = 0
        self.has_known_extends = False
        self._last_line = 0
        self._first_write = True

    def temporary_identifier(self):
        self.last_identifier += 1
        return 't%d' % self.last_identifier

    def indent(self):
        self.indentation += 1

    def outdent(self, step=1):
        self.indentation -= step

    def blockvisit(self, nodes, frame, force_generator=False):
        self.indent()
        if force_generator:
            self.writeline('if 0: yield None')
        try:
            for node in nodes:
                self.visit(node, frame)
        except CompilerExit:
            pass
        self.outdent()

    def write(self, x):
        if self.new_lines:
            if not self._first_write:
                self.stream.write('\n' * self.new_lines)
            self._first_write = False
            self.stream.write('    ' * self.indentation)
            self.new_lines = 0
        self.stream.write(x)

    def writeline(self, x, node=None, extra=0):
        self.newline(node, extra)
        self.write(x)

    def newline(self, node=None, extra=0):
        self.new_lines = max(self.new_lines, 1 + extra)
        if node is not None and node.lineno != self._last_line:
            self.write('# line: %s' % node.lineno)
            self.new_lines = 1
            self._last_line = node.lineno

    def signature(self, node, frame, have_comma=True):
        have_comma = have_comma and [True] or []
        def touch_comma():
            if have_comma:
                self.write(', ')
            else:
                have_comma.append(True)

        for arg in node.args:
            touch_comma()
            self.visit(arg, frame)
        for kwarg in node.kwargs:
            touch_comma()
            self.visit(kwarg, frame)
        if node.dyn_args:
            touch_comma()
            self.visit(node.dyn_args, frame)
        if node.dyn_kwargs:
            touch_comma()
            self.visit(node.dyn_kwargs, frame)

    def pull_locals(self, frame, no_indent=False):
        if not no_indent:
            self.indent()
        for name in frame.identifiers.undeclared:
            self.writeline('l_%s = context[%r]' % (name, name))
        for name, count in frame.identifiers.undeclared_filter.iteritems():
            if count > 1:
                self.writeline('f_%s = environment.filters[%r]' % (name, name))
        if not no_indent:
            self.outdent()

    # -- Visitors

    def visit_Template(self, node, frame=None):
        assert frame is None, 'no root frame allowed'
        self.writeline('from jinja2.runtime import *')
        self.writeline('filename = %r' % self.filename)

        # do we have an extends tag at all?  If not, we can save some
        # overhead by just not processing any inheritance code.
        have_extends = node.find(nodes.Extends) is not None

        # find all blocks
        for block in node.find_all(nodes.Block):
            if block.name in self.blocks:
                raise TemplateAssertionError('block %r defined twice' %
                                             block.name, block.lineno,
                                             self.filename)
            self.blocks[block.name] = block

        # generate the root render function.
        self.writeline('def root(globals):', extra=1)
        self.indent()
        self.writeline('context = TemplateContext(globals, filename, blocks)')
        if have_extends:
            self.writeline('parent_root = None')
        self.outdent()

        # process the root
        frame = Frame()
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True
        self.pull_locals(frame)
        self.blockvisit(node.body, frame, True)

        # make sure that the parent root is called.
        if have_extends:
            if not self.has_known_extends:
                self.indent()
                self.writeline('if parent_root is not None:')
            self.indent()
            self.writeline('for event in parent_root(context):')
            self.indent()
            self.writeline('yield event')
            self.outdent(1 + self.has_known_extends)

        # at this point we now have the blocks collected and can visit them too.
        for name, block in self.blocks.iteritems():
            block_frame = Frame()
            block_frame.inspect(block.body)
            block_frame.block = name
            self.writeline('def block_%s(context):' % name, block, 1)
            self.pull_locals(block_frame)
            self.blockvisit(block.body, block_frame, True)

        self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
                                                   for x in self.blocks), extra=1)

    def visit_Block(self, node, frame):
        """Call a block and register it for the template."""
        if frame.toplevel:
            # if we know that we are a child template, there is no need to
            # check if we are one
            if self.has_known_extends:
                return
            self.writeline('if parent_root is None:')
            self.indent()
        self.writeline('for event in context.blocks[0][%r](context):' % node.name)
        self.indent()
        self.writeline('yield event')
        self.outdent(1 + frame.toplevel)

    def visit_Extends(self, node, frame):
        """Calls the extender."""
        if not frame.toplevel:
            raise TemplateAssertionError('cannot use extend from a non '
                                         'top-level scope', node.lineno,
                                         self.filename)

        # if the number of extends statements in general is zero so
        # far, we don't have to add a check if something extended
        # the template before this one.
        if self.extends_so_far > 0:

            # if we have a known extends we just add a template runtime
            # error into the generated code.  We could catch that at compile
            # time too, but i welcome it not to confuse users by throwing the
            # same error at different times just "because we can".
            if not self.has_known_extends:
                self.writeline('if parent_root is not None:')
                self.indent()
            self.writeline('raise TemplateRuntimeError(%r)' %
                           'extended multiple times')

            # if we have a known extends already we don't need that code here
            # as we know that the template execution will end here.
            if self.has_known_extends:
                raise CompilerExit()
            self.outdent()

        self.writeline('parent_root = extends(', node, 1)
        self.visit(node.template, frame)
        self.write(', context, environment)')

        # if this extends statement was in the root level we can take
        # advantage of that information and simplify the generated code
        # in the top level from this point onwards
        self.has_known_extends = True

        # and now we have one more
        self.extends_so_far += 1

    def visit_For(self, node, frame):
        loop_frame = frame.inner()
        loop_frame.inspect(node.iter_child_nodes())
        extended_loop = bool(node.else_) or \
                        'loop' in loop_frame.identifiers.undeclared
        loop_frame.identifiers.add_special('loop')

        # make sure we "backup" overridden, local identifiers
        # TODO: we should probably optimize this and check if the
        # identifier is in use afterwards.
        aliases = {}
        for name in loop_frame.identifiers.find_shadowed():
            aliases[name] = ident = self.temporary_identifier()
            self.writeline('%s = l_%s' % (ident, name))

        self.pull_locals(loop_frame, True)

        self.newline(node)
        if node.else_:
            self.writeline('l_loop = None')
        self.write('for ')
        self.visit(node.target, loop_frame)
        self.write(extended_loop and ', l_loop in LoopContext(' or ' in ')
        self.visit(node.iter, loop_frame)
        if 'loop' in aliases:
            self.write(', ' + aliases['loop'])
        self.write(extended_loop and '):' or ':')
        self.blockvisit(node.body, loop_frame)

        if node.else_:
            self.writeline('if l_loop is None:')
            self.blockvisit(node.else_, loop_frame)

        # reset the aliases and clean up
        delete = set('l_' + x for x in loop_frame.identifiers.declared_locally
                     | loop_frame.identifiers.declared_parameter)
        if extended_loop:
            delete.add('l_loop')
        for name, alias in aliases.iteritems():
            self.writeline('l_%s = %s' % (name, alias))
            delete.add(alias)
            delete.discard('l_' + name)
        self.writeline('del %s' % ', '.join(delete))

    def visit_If(self, node, frame):
        if_frame = frame.soft()
        self.writeline('if ', node)
        self.visit(node.test, if_frame)
        self.write(':')
        self.blockvisit(node.body, if_frame)
        if node.else_:
            self.writeline('else:')
            self.blockvisit(node.else_, if_frame)

    def visit_Macro(self, node, frame):
        macro_frame = frame.inner()
        macro_frame.inspect(node.iter_child_nodes(), hard_scope=True)

        # variables that are undeclared (accessed before declaration) and
        # declared locally *and* part of an outside scope raise a template
        # assertion error. Reason: we can't generate reasonable code from
        # it without aliasing all the variables.  XXX: alias them ^^
        overriden_closure_vars = (
            macro_frame.identifiers.undeclared &
            macro_frame.identifiers.declared &
            (macro_frame.identifiers.declared_locally |
             macro_frame.identifiers.declared_parameter)
        )
        if overriden_closure_vars:
            vars = ', '.join(sorted(overriden_closure_vars))
            raise TemplateAssertionError('It\'s not possible to set and '
                                         'access variables derived from '
                                         'an outer scope! (affects: %s' %
                                         vars, node.lineno, self.filename)

        # remove variables from a closure from the frame's undeclared
        # identifiers.
        macro_frame.identifiers.undeclared -= (
            macro_frame.identifiers.undeclared &
            macro_frame.identifiers.declared
        )

        args = ['l_' + x.name for x in node.args]
        if 'arguments' in macro_frame.identifiers.undeclared:
            accesses_arguments = True
            args.append('l_arguments')
        else:
            accesses_arguments = False
        self.writeline('def macro(%s):' % ', '.join(args), node)
        self.indent()
        self.writeline('if 0: yield None')
        self.outdent()
        self.pull_locals(macro_frame)
        self.blockvisit(node.body, macro_frame)
        self.newline()
        if frame.toplevel:
            self.write('context[%r] = ' % node.name)
        arg_tuple = ', '.join(repr(x.name) for x in node.args)
        if len(node.args) == 1:
            arg_tuple += ','
        self.write('l_%s = Macro(macro, %r, (%s), (' % (node.name, node.name,
                                                       arg_tuple))
        for arg in node.defaults:
            self.visit(arg)
            self.write(', ')
        self.write('), %r)' % accesses_arguments)

    def visit_ExprStmt(self, node, frame):
        self.newline(node)
        self.visit(node, frame)

    def visit_Output(self, node, frame):
        # if we have a known extends statement, we don't output anything
        if self.has_known_extends and frame.toplevel:
            return

        self.newline(node)
        if self.environment.finalize is unicode:
            finalizer = 'unicode'
        else:
            finalizer = 'context.finalize'

        # if we are in the toplevel scope and there was already an extends
        # statement we have to add a check that disables our yield(s) here
        # so that they don't appear in the output.
        outdent_later = False
        if frame.toplevel and self.extends_so_far != 0:
            self.writeline('if parent_root is None:')
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

        # if we have less than 3 nodes we just yield them
        if len(body) < 3:
            for item in body:
                if isinstance(item, list):
                    self.writeline('yield %s' % repr(u''.join(item)))
                else:
                    self.newline(item)
                    self.write('yield %s(' % finalizer)
                    self.visit(item, frame)
                    self.write(')')

        # otherwise we create a format string as this is faster in that case
        else:
            format = []
            arguments = []
            for item in body:
                if isinstance(item, list):
                    format.append(u''.join(item).replace('%', '%%'))
                else:
                    format.append('%s')
                    arguments.append(item)
            self.writeline('yield %r %% (' % u''.join(format))
            idx = -1
            for idx, argument in enumerate(arguments):
                if idx:
                    self.write(', ')
                if finalizer != 'unicode':
                    self.write('(')
                self.visit(argument, frame)
                if finalizer != 'unicode':
                    self.write(')')
            self.write(idx == 0 and ',)' or ')')

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
            for name in assignment_frame.assigned_names:
                self.writeline('context[%r] = l_%s' % (name, name))

    def visit_Name(self, node, frame):
        if frame.toplevel and node.ctx == 'store':
            frame.assigned_names.add(node.name)
        self.write('l_' + node.name)

    def visit_Const(self, node, frame):
        val = node.value
        if isinstance(val, float):
            # XXX: add checks for infinity and nan
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
            self.visit(node.node)
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

    def visit_Compare(self, node, frame):
        self.visit(node.expr, frame)
        for op in node.ops:
            self.visit(op, frame)

    def visit_Operand(self, node, frame):
        self.write(' %s ' % operators[node.op])
        self.visit(node.expr, frame)

    def visit_Subscript(self, node, frame):
        if isinstance(node.arg, nodes.Slice):
            self.visit(node.node, frame)
            self.write('[')
            self.visit(node.arg, frame)
            self.write(']')
            return
        try:
            const = node.arg.as_const()
            have_const = True
        except nodes.Impossible:
            have_const = False
        if have_const:
            if isinstance(const, (int, long, float)):
                self.visit(node.node, frame)
                self.write('[%s]' % const)
                return
        self.write('subscribe(')
        self.visit(node.node, frame)
        self.write(', ')
        if have_const:
            self.write(repr(const))
        else:
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

    def visit_Filter(self, node, frame):
        if node.name in frame.identifiers.declared_filter:
            self.write('f_%s(' % node.name)
        else:
            self.write('environment.filters[%r](' % node.name)
        self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    def visit_Test(self, node, frame):
        self.write('environment.tests[%r](')
        self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    def visit_Call(self, node, frame):
        self.visit(node.node, frame)
        self.write('(')
        self.signature(node, frame, False)
        self.write(')')

    def visit_Keyword(self, node, frame):
        self.visit(node.key, frame)
        self.write('=')
        self.visit(node.value, frame)
