# -*- coding: utf-8 -*-
"""
    jinja2.nodes
    ~~~~~~~~~~~~

    This module implements additional nodes derived from the ast base node.

    It also provides some node tree helper functions like `in_lineno` and
    `get_nodes` used by the parser and translator in order to normalize
    python and jinja nodes.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import operator
from itertools import chain, izip
from collections import deque
from copy import copy


_binop_to_func = {
    '*':        operator.mul,
    '/':        operator.truediv,
    '//':       operator.floordiv,
    '**':       operator.pow,
    '%':        operator.mod,
    '+':        operator.add,
    '-':        operator.sub
}

_uaop_to_func = {
    'not':      operator.not_,
    '+':        operator.pos,
    '-':        operator.neg
}


def set_ctx(node, ctx):
    """
    Reset the context of a node and all child nodes.  Per default the parser
    will all generate nodes that have a 'load' context as it's the most common
    one.  This method is used in the parser to set assignment targets and
    other nodes to a store context.
    """
    todo = deque([node])
    while todo:
        node = todo.popleft()
        if 'ctx' in node._fields:
            node.ctx = ctx
        todo.extend(node.iter_child_nodes())


class Impossible(Exception):
    """
    Raised if the node could not perform a requested action.
    """


class NodeType(type):

    def __new__(cls, name, bases, d):
        for attr in '_fields', '_attributes':
            storage = []
            for base in bases:
                storage.extend(getattr(base, attr, ()))
            storage.extend(d.get(attr, ()))
            assert len(storage) == len(set(storage))
            d[attr] = tuple(storage)
        return type.__new__(cls, name, bases, d)


class Node(object):
    """
    Base jinja node.
    """
    __metaclass__ = NodeType
    _fields = ()
    _attributes = ('lineno',)

    def __init__(self, *args, **kw):
        if args:
            if len(args) != len(self._fields):
                if not self._fields:
                    raise TypeError('%r takes 0 arguments' %
                                    self.__class__.__name__)
                raise TypeError('%r takes 0 or %d argument%s' % (
                    self.__class__.__name__,
                    len(self._fields),
                    len(self._fields) != 1 and 's' or ''
                ))
            for name, arg in izip(self._fields, args):
                setattr(self, name, arg)
        for attr in self._attributes:
            setattr(self, attr, kw.pop(attr, None))
        if kw:
            raise TypeError('unknown keyword argument %r' %
                            iter(kw).next())

    def iter_fields(self):
        for name in self._fields:
            try:
                yield name, getattr(self, name)
            except AttributeError:
                pass

    def iter_child_nodes(self):
        for field, item in self.iter_fields():
            if isinstance(item, list):
                for n in item:
                    if isinstance(n, Node):
                        yield n
            elif isinstance(item, Node):
                yield item

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (arg, getattr(self, arg, None)) for
                      arg in self._fields)
        )


class Stmt(Node):
    """
    Base node for all statements.
    """


class Helper(Node):
    """
    Nodes that exist in a specific context only.
    """


class Template(Node):
    """
    Node that represents a template.
    """
    _fields = ('body',)


class Output(Stmt):
    """
    A node that holds multiple expressions which are then printed out.  This
    is used both for the `print` statement and the regular template data.
    """
    _fields = ('nodes',)


class Extends(Stmt):
    """
    Represents an extends statement.
    """
    _fields = ('extends',)


class For(Stmt):
    """
    A node that represents a for loop
    """
    _fields = ('target', 'iter', 'body', 'else_', 'recursive')


class If(Stmt):
    """
    A node that represents an if condition.
    """
    _fields = ('test', 'body', 'else_')


class Macro(Stmt):
    """
    A node that represents a macro.
    """
    _fields = ('name', 'arguments', 'body')


class CallBlock(Stmt):
    """
    A node that represents am extended macro call.
    """
    _fields = ('expr', 'body')


class Set(Stmt):
    """
    Allows defining own variables.
    """
    _fields = ('name', 'expr')


class FilterBlock(Stmt):
    """
    Node for filter sections.
    """
    _fields = ('body', 'filters')


class Block(Stmt):
    """
    A node that represents a block.
    """
    _fields = ('name', 'body')


class Include(Stmt):
    """
    A node that represents the include tag.
    """
    _fields = ('template',)


class Trans(Stmt):
    """
    A node for translatable sections.
    """
    _fields = ('singular', 'plural', 'indicator', 'replacements')


class ExprStmt(Stmt):
    """
    A statement that evaluates an expression to None.
    """
    _fields = ('node',)


class Assign(Stmt):
    """
    Assigns an expression to a target.
    """
    _fields = ('target', 'node')


class Expr(Node):
    """
    Baseclass for all expressions.
    """

    def as_const(self):
        """
        Return the value of the expression as constant or raise `Impossible`
        if this was not possible.
        """
        raise Impossible()

    def can_assign(self):
        """
        Check if it's possible to assign something to this node.
        """
        return False


class BinExpr(Expr):
    """
    Baseclass for all binary expressions.
    """
    _fields = ('left', 'right')
    operator = None

    def as_const(self):
        f = _binop_to_func[self.operator]
        try:
            return f(self.left.as_const(), self.right.as_const())
        except:
            print self.left, f, self.right
            raise Impossible()


class UnaryExpr(Expr):
    """
    Baseclass for all unary expressions.
    """
    _fields = ('node',)
    operator = None

    def as_const(self):
        f = _uaop_to_func[self.operator]
        try:
            return f(self.node.as_const())
        except:
            raise Impossible()


class Name(Expr):
    """
    any name such as {{ foo }}
    """
    _fields = ('name', 'ctx')

    def can_assign(self):
        return True


class Literal(Expr):
    """
    Baseclass for literals.
    """


class Const(Literal):
    """
    any constat such as {{ "foo" }}
    """
    _fields = ('value',)

    def as_const(self):
        return self.value


class Tuple(Literal):
    """
    For loop unpacking and some other things like multiple arguments
    for subscripts.
    """
    _fields = ('items', 'ctx')

    def as_const(self):
        return tuple(x.as_const() for x in self.items)

    def can_assign(self):
        for item in self.items:
            if not item.can_assign():
                return False
        return True


class List(Literal):
    """
    any list literal such as {{ [1, 2, 3] }}
    """
    _fields = ('items',)

    def as_const(self):
        return [x.as_const() for x in self.items]


class Dict(Literal):
    """
    any dict literal such as {{ {1: 2, 3: 4} }}
    """
    _fields = ('items',)

    def as_const(self):
        return dict(x.as_const() for x in self.items)


class Pair(Helper):
    """
    A key, value pair for dicts.
    """
    _fields = ('key', 'value')

    def as_const(self):
        return self.key.as_const(), self.value.as_const()


class CondExpr(Expr):
    """
    {{ foo if bar else baz }}
    """
    _fields = ('test', 'expr1', 'expr2')

    def as_const(self):
        if self.test.as_const():
            return self.expr1.as_const()
        return self.expr2.as_const()


class Filter(Expr):
    """
    {{ foo|bar|baz }}
    """
    _fields = ('node', 'filters')


class FilterCall(Expr):
    """
    {{ |bar() }}
    """
    _fields = ('name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Test(Expr):
    """
    {{ foo is lower }}
    """
    _fields = ('name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Call(Expr):
    """
    {{ foo(bar) }}
    """
    _fields = ('node', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Subscript(Expr):
    """
    {{ foo.bar }} and {{ foo['bar'] }} etc.
    """
    _fields = ('node', 'arg', 'ctx')

    def as_const(self):
        try:
            return self.node.as_const()[self.node.as_const()]
        except:
            raise Impossible()

    def can_assign(self):
        return True


class Slice(Expr):
    """
    1:2:3 etc.
    """
    _fields = ('start', 'stop', 'step')


class Concat(Expr):
    """
    For {{ foo ~ bar }}.  Concatenates strings.
    """
    _fields = ('nodes',)

    def as_const(self):
        return ''.join(unicode(x.as_const()) for x in self.nodes)


class Compare(Expr):
    """
    {{ foo == bar }}, {{ foo >= bar }} etc.
    """
    _fields = ('expr', 'ops')


class Operand(Helper):
    """
    Operator + expression.
    """
    _fields = ('op', 'expr')


class Mul(BinExpr):
    """
    {{ foo * bar }}
    """
    operator = '*'


class Div(BinExpr):
    """
    {{ foo / bar }}
    """
    operator = '/'


class FloorDiv(BinExpr):
    """
    {{ foo // bar }}
    """
    operator = '//'


class Add(BinExpr):
    """
    {{ foo + bar }}
    """
    operator = '+'


class Sub(BinExpr):
    """
    {{ foo - bar }}
    """
    operator = '-'


class Mod(BinExpr):
    """
    {{ foo % bar }}
    """
    operator = '%'


class Pow(BinExpr):
    """
    {{ foo ** bar }}
    """
    operator = '**'


class And(BinExpr):
    """
    {{ foo and bar }}
    """
    operator = 'and'

    def as_const(self):
        return self.left.as_const() and self.right.as_const()


class Or(BinExpr):
    """
    {{ foo or bar }}
    """
    operator = 'or'

    def as_const(self):
        return self.left.as_const() or self.right.as_const()


class Not(UnaryExpr):
    """
    {{ not foo }}
    """
    operator = 'not'


class NegExpr(UnaryExpr):
    """
    {{ -foo }}
    """
    operator = '-'


class PosExpr(UnaryExpr):
    """
    {{ +foo }}
    """
    operator = '+'
