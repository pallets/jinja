# -*- coding: utf-8 -*-
"""
    jinja2.compiler
    ~~~~~~~~~~~~~~~

    Compiles nodes into python code.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
from random import randrange
from operator import xor
from cStringIO import StringIO
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.exceptions import TemplateAssertionError


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


def generate(node, filename, stream=None):
    is_child = node.find(nodes.Extends) is not None
    generator = CodeGenerator(is_child, filename, stream)
    generator.visit(node)
    if stream is None:
        return generator.stream.getvalue()


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

    def add_special(self, name):
        """Register a special name like `loop`."""
        self.undeclared.discard(name)
        self.declared.add(name)

    def is_declared(self, name):
        """Check if a name is declared in this or an outer scope."""
        return name in self.declared or name in self.declared_locally or \
               name in self.declared_parameter

    def find_shadowed(self):
        """Find all the shadowed names."""
        return self.declared & (self.declared_locally | self.declared_parameter)


class Frame(object):

    def __init__(self, parent=None):
        self.identifiers = Identifiers()
        self.parent = parent
        if parent is not None:
            self.identifiers.declared.update(
                parent.identifiers.declared |
                parent.identifiers.undeclared |
                parent.identifiers.declared_locally |
                parent.identifiers.declared_parameter
            )

    def inspect(self, nodes):
        """Walk the node and check for identifiers."""
        visitor = FrameIdentifierVisitor(self.identifiers)
        for node in nodes:
            visitor.visit(node)

    def inner(self):
        """Return an inner frame."""
        return Frame(self)


class FrameIdentifierVisitor(NodeVisitor):
    """A visitor for `Frame.inspect`."""

    def __init__(self, identifiers):
        self.identifiers = identifiers

    def visit_Name(self, node):
        """All assignments to names go through this function."""
        if node.ctx in ('store', 'param'):
            self.identifiers.declared_locally.add(node.name)
        elif node.ctx == 'load':
            if not self.identifiers.is_declared(node.name):
                self.identifiers.undeclared.add(node.name)

    def visit_Macro(self, node):
        """Macros set local."""
        self.identifiers.declared_locally.add(node.name)

    # stop traversing at instructions that have their own scope.
    visit_Block = visit_Call = visit_FilterBlock = \
        visit_For = lambda s, n: None


class CodeGenerator(NodeVisitor):

    def __init__(self, is_child, filename, stream=None):
        if stream is None:
            stream = StringIO()
        self.is_child = is_child
        self.filename = filename
        self.stream = stream
        self.blocks = {}
        self.indentation = 0
        self.new_lines = 0
        self.last_identifier = 0
        self._last_line = 0
        self._first_write = True

    def temporary_identifier(self):
        self.last_identifier += 1
        return 't%d' % self.last_identifier

    def indent(self):
        self.indentation += 1

    def outdent(self):
        self.indentation -= 1

    def blockvisit(self, nodes, frame, force_generator=False):
        self.indent()
        if force_generator:
            self.writeline('if 0: yield None')
        for node in nodes:
            self.visit(node, frame)
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

    def pull_locals(self, frame, no_indent=False):
        if not no_indent:
            self.indent()
        for name in frame.identifiers.undeclared:
            self.writeline('l_%s = context[%r]' % (name, name))
        if not no_indent:
            self.outdent()

    # -- Visitors

    def visit_Template(self, node, frame=None):
        assert frame is None, 'no root frame allowed'
        self.writeline('from jinja2.runtime import *')
        self.writeline('filename = %r' % self.filename)
        self.writeline('context = TemplateContext(global_context, '
                       'make_undefined, filename)')

        # generate the body render function.
        self.writeline('def body(context=context):', extra=1)
        frame = Frame()
        frame.inspect(node.body)
        self.pull_locals(frame)
        self.blockvisit(node.body, frame, True)

        # top level changes to locals are pushed back to the
        # context of *this* template for include.
        self.indent()
        self.writeline('context.from_locals(locals())')
        self.outdent()

        # at this point we now have the blocks collected and can visit them too.
        for name, block in self.blocks.iteritems():
            block_frame = Frame()
            block_frame.inspect(block.body)
            self.writeline('def block_%s(context=context):' % name, block, 1)
            self.pull_locals(block_frame)
            self.blockvisit(block.body, block_frame, True)

    def visit_Block(self, node, frame):
        """Call a block and register it for the template."""
        if node.name in self.blocks:
            raise TemplateAssertionError("the block '%s' was already defined" %
                                         node.name, node.lineno,
                                         self.filename)
        self.blocks[node.name] = node
        self.writeline('for event in block_%s():' % node.name)
        self.indent()
        self.writeline('yield event')
        self.outdent()

    def visit_Extends(self, node, frame):
        """Calls the extender."""
        self.writeline('extends(', node, 1)
        self.visit(node.template)
        self.write(', globals())')

    def visit_For(self, node, frame):
        loop_frame = frame.inner()
        loop_frame.inspect(node.iter_child_nodes())
        loop_frame.identifiers.add_special('loop')
        extended_loop = bool(node.else_) or \
                        'loop' in loop_frame.identifiers.undeclared

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
        self.write(extended_loop and ', l_loop in looper(' or ' in ')
        self.visit(node.iter, loop_frame)
        self.write(extended_loop and '):' or ':')
        self.blockvisit(node.body, loop_frame)

        if node.else_:
            self.writeline('if l_loop is None:')
            self.blockvisit(node.else_, loop_frame)

        # reset the aliases and clean them up
        for name, alias in aliases.iteritems():
            self.writeline('l_%s = %s; del %s' % (name, alias, alias))

    def visit_If(self, node, frame):
        self.writeline('if ', node)
        self.visit(node.test, frame)
        self.write(':')
        self.blockvisit(node.body, frame)
        if node.else_:
            self.writeline('else:')
            self.blockvisit(node.else_, frame)

    def visit_ExprStmt(self, node, frame):
        self.newline(node)
        self.visit(node, frame)

    def visit_Output(self, node, frame):
        self.newline(node)

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
                    self.write('yield unicode(')
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
                self.visit(argument, frame)
            self.write(idx == 0 and ',)' or ')')

    def visit_Name(self, node, frame):
        # at this point we should only have locals left as the
        # blocks, macros and template body ensure that they are set.
        self.write('l_' + node.name)

    def visit_Const(self, node, frame):
        val = node.value
        if isinstance(val, float):
            # XXX: add checks for infinity and nan
            self.write(str(val))
        else:
            self.write(repr(val))

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
        self.write('subscript(')
        self.visit(node.node, frame)
        self.write(', ')
        self.visit(node.arg, frame)
        self.write(')')
