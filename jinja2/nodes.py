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

_cmpop_to_func = {
    'eq':       operator.eq,
    'ne':       operator.ne,
    'gt':       operator.gt,
    'gteq':     operator.ge,
    'lt':       operator.lt,
    'lteq':     operator.le,
    'in':       operator.contains,
    'notin':    lambda a, b: not operator.contains(a, b)
}


class Impossible(Exception):
    """Raised if the node could not perform a requested action."""


class NodeType(type):
    """A metaclass for nodes that handles the field and attribute
    inheritance.  fields and attributes from the parent class are
    automatically forwarded to the child."""

    def __new__(cls, name, bases, d):
        for attr in 'fields', 'attributes':
            storage = []
            storage.extend(getattr(bases[0], attr, ()))
            storage.extend(d.get(attr, ()))
            assert len(bases) == 1, 'multiple inheritance not allowed'
            assert len(storage) == len(set(storage)), 'layout conflict'
            d[attr] = tuple(storage)
        return type.__new__(cls, name, bases, d)


class Node(object):
    """Baseclass for all Jinja nodes."""
    __metaclass__ = NodeType
    fields = ()
    attributes = ('lineno', 'environment')

    def __init__(self, *args, **kw):
        if args:
            if len(args) != len(self.fields):
                if not self.fields:
                    raise TypeError('%r takes 0 arguments' %
                                    self.__class__.__name__)
                raise TypeError('%r takes 0 or %d argument%s' % (
                    self.__class__.__name__,
                    len(self.fields),
                    len(self.fields) != 1 and 's' or ''
                ))
            for name, arg in izip(self.fields, args):
                setattr(self, name, arg)
        for attr in self.attributes:
            setattr(self, attr, kw.pop(attr, None))
        if kw:
            raise TypeError('unknown keyword argument %r' %
                            iter(kw).next())

    def iter_fields(self):
        """Iterate over all fields."""
        for name in self.fields:
            try:
                yield name, getattr(self, name)
            except AttributeError:
                pass

    def iter_child_nodes(self):
        """Iterate over all child nodes."""
        for field, item in self.iter_fields():
            if isinstance(item, list):
                for n in item:
                    if isinstance(n, Node):
                        yield n
            elif isinstance(item, Node):
                yield item

    def find(self, node_type):
        """Find the first node of a given type."""
        for result in self.find_all(node_type):
            return result

    def find_all(self, node_type):
        """Find all the nodes of a given type."""
        for child in self.iter_child_nodes():
            if isinstance(child, node_type):
                yield child
            for result in child.find_all(node_type):
                yield result

    def copy(self):
        """Return a deep copy of the node."""
        result = object.__new__(self.__class__)
        for field, value in self.iter_fields():
            if isinstance(value, Node):
                new_value = value.copy()
            elif isinstance(value, list):
                new_value = []
                for item in value:
                    if isinstance(item, Node):
                        item = item.copy()
                    else:
                        item = copy(item)
                    new_value.append(item)
            else:
                new_value = copy(value)
            setattr(result, field, new_value)
        for attr in self.attributes:
            try:
                setattr(result, attr, getattr(self, attr))
            except AttributeError:
                pass
        return result

    def set_ctx(self, ctx):
        """Reset the context of a node and all child nodes.  Per default the
        parser will all generate nodes that have a 'load' context as it's the
        most common one.  This method is used in the parser to set assignment
        targets and other nodes to a store context.
        """
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if 'ctx' in node.fields:
                node.ctx = ctx
            todo.extend(node.iter_child_nodes())

    def set_lineno(self, lineno, override=False):
        """Set the line numbers of the node and children."""
        todo = deque([self])
        while todo:
            node = todo.popleft()
            if 'lineno' in node.attributes:
                if node.lineno is None or override:
                    node.lineno = lineno
            todo.extend(node.iter_child_nodes())

    def set_environment(self, environment):
        """Set the environment for all nodes."""
        todo = deque([self])
        while todo:
            node = todo.popleft()
            node.environment = environment
            todo.extend(node.iter_child_nodes())

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (arg, getattr(self, arg, None)) for
                      arg in self.fields)
        )


class Stmt(Node):
    """Base node for all statements."""


class Helper(Node):
    """Nodes that exist in a specific context only."""


class Template(Node):
    """Node that represents a template."""
    fields = ('body',)


class Output(Stmt):
    """A node that holds multiple expressions which are then printed out.
    This is used both for the `print` statement and the regular template data.
    """
    fields = ('nodes',)

    def optimized_nodes(self):
        """Try to optimize the nodes."""
        buffer = []
        for node in self.nodes:
            try:
                const = unicode(node.as_const())
            except:
                buffer.append(node)
            else:
                if buffer and isinstance(buffer[-1], unicode):
                    buffer[-1] += const
                else:
                    buffer.append(const)
        return buffer


class Extends(Stmt):
    """Represents an extends statement."""
    fields = ('template',)


class For(Stmt):
    """A node that represents a for loop"""
    fields = ('target', 'iter', 'body', 'else_', 'test')


class If(Stmt):
    """A node that represents an if condition."""
    fields = ('test', 'body', 'else_')


class Macro(Stmt):
    """A node that represents a macro."""
    fields = ('name', 'args', 'defaults', 'body')


class CallBlock(Stmt):
    """A node that represents am extended macro call."""
    fields = ('call', 'args', 'defaults', 'body')


class Set(Stmt):
    """Allows defining own variables."""
    fields = ('name', 'expr')


class FilterBlock(Stmt):
    """Node for filter sections."""
    fields = ('body', 'filter')


class Block(Stmt):
    """A node that represents a block."""
    fields = ('name', 'body')


class Include(Stmt):
    """A node that represents the include tag."""
    fields = ('template', 'target')


class Trans(Stmt):
    """A node for translatable sections."""
    fields = ('singular', 'plural', 'indicator', 'replacements')


class ExprStmt(Stmt):
    """A statement that evaluates an expression to None."""
    fields = ('node',)


class Assign(Stmt):
    """Assigns an expression to a target."""
    fields = ('target', 'node')


class Expr(Node):
    """Baseclass for all expressions."""

    def as_const(self):
        """Return the value of the expression as constant or raise
        `Impossible` if this was not possible.
        """
        raise Impossible()

    def can_assign(self):
        """Check if it's possible to assign something to this node."""
        return False


class BinExpr(Expr):
    """Baseclass for all binary expressions."""
    fields = ('left', 'right')
    operator = None

    def as_const(self):
        f = _binop_to_func[self.operator]
        try:
            return f(self.left.as_const(), self.right.as_const())
        except:
            raise Impossible()


class UnaryExpr(Expr):
    """Baseclass for all unary expressions."""
    fields = ('node',)
    operator = None

    def as_const(self):
        f = _uaop_to_func[self.operator]
        try:
            return f(self.node.as_const())
        except:
            raise Impossible()


class Name(Expr):
    """any name such as {{ foo }}"""
    fields = ('name', 'ctx')

    def can_assign(self):
        return self.name not in ('true', 'false', 'none')


class Literal(Expr):
    """Baseclass for literals."""


class Const(Literal):
    """any constat such as {{ "foo" }}"""
    fields = ('value',)

    def as_const(self):
        return self.value

    @classmethod
    def from_untrusted(cls, value, lineno=None, environment=None):
        """Return a const object if the value is representable as
        constant value in the generated code, otherwise it will raise
        an `Impossible` exception.
        """
        from compiler import has_safe_repr
        if not has_safe_repr(value):
            raise Impossible()
        return cls(value, lineno=lineno, environment=environment)


class Tuple(Literal):
    """For loop unpacking and some other things like multiple arguments
    for subscripts.
    """
    fields = ('items', 'ctx')

    def as_const(self):
        return tuple(x.as_const() for x in self.items)

    def can_assign(self):
        for item in self.items:
            if not item.can_assign():
                return False
        return True


class List(Literal):
    """any list literal such as {{ [1, 2, 3] }}"""
    fields = ('items',)

    def as_const(self):
        return [x.as_const() for x in self.items]


class Dict(Literal):
    """any dict literal such as {{ {1: 2, 3: 4} }}"""
    fields = ('items',)

    def as_const(self):
        return dict(x.as_const() for x in self.items)


class Pair(Helper):
    """A key, value pair for dicts."""
    fields = ('key', 'value')

    def as_const(self):
        return self.key.as_const(), self.value.as_const()


class Keyword(Helper):
    """A key, value pair for keyword arguments."""
    fields = ('key', 'value')


class CondExpr(Expr):
    """{{ foo if bar else baz }}"""
    fields = ('test', 'expr1', 'expr2')

    def as_const(self):
        if self.test.as_const():
            return self.expr1.as_const()
        return self.expr2.as_const()


class Filter(Expr):
    """{{ foo|bar|baz }}"""
    fields = ('node', 'name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')

    def as_const(self, obj=None):
        if self.node is obj is None:
            raise Impossible()
        filter = self.environment.filters.get(self.name)
        if filter is None or getattr(filter, 'contextfilter', False):
            raise Impossible()
        if obj is None:
            obj = self.node.as_const()
        args = [x.as_const() for x in self.args]
        if getattr(filter, 'environmentfilter', False):
            args.insert(0, self.environment)
        kwargs = dict(x.as_const() for x in self.kwargs)
        if self.dyn_args is not None:
            try:
                args.extend(self.dyn_args.as_const())
            except:
                raise Impossible()
        if self.dyn_kwargs is not None:
            try:
                kwargs.update(self.dyn_kwargs.as_const())
            except:
                raise Impossible()
        try:
            return filter(obj, *args, **kwargs)
        except:
            raise Impossible()


class Test(Expr):
    """{{ foo is lower }}"""
    fields = ('node', 'name', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')


class Call(Expr):
    """{{ foo(bar) }}"""
    fields = ('node', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')

    def as_const(self):
        obj = self.node.as_const()
        args = [x.as_const() for x in self.args]
        kwargs = dict(x.as_const() for x in self.kwargs)
        if self.dyn_args is not None:
            try:
                args.extend(self.dyn_args.as_const())
            except:
                raise Impossible()
        if self.dyn_kwargs is not None:
            try:
                kwargs.update(self.dyn_kwargs.as_const())
            except:
                raise Impossible()
        try:
            return obj(*args, **kwargs)
        except:
            raise Impossible()


class Subscript(Expr):
    """{{ foo.bar }} and {{ foo['bar'] }} etc."""
    fields = ('node', 'arg', 'ctx')

    def as_const(self):
        if self.ctx != 'load':
            raise Impossible()
        try:
            return environmen.subscribe(self.node.as_const(), self.arg.as_const())
        except:
            raise Impossible()

    def can_assign(self):
        return True


class Slice(Expr):
    """1:2:3 etc."""
    fields = ('start', 'stop', 'step')

    def as_const(self):
        def const(obj):
            if obj is None:
                return obj
            return obj.as_const()
        return slice(const(self.start), const(self.stop), const(self.step))


class Concat(Expr):
    """For {{ foo ~ bar }}.  Concatenates strings."""
    fields = ('nodes',)

    def as_const(self):
        return ''.join(unicode(x.as_const()) for x in self.nodes)


class Compare(Expr):
    """{{ foo == bar }}, {{ foo >= bar }} etc."""
    fields = ('expr', 'ops')

    def as_const(self):
        result = value = self.expr.as_const()
        for op in self.ops:
            new_value = op.expr.as_const()
            result = _cmpop_to_func[op.op](value, new_value)
            value = new_value
        return result


class Operand(Helper):
    """Operator + expression."""
    fields = ('op', 'expr')


class Mul(BinExpr):
    """{{ foo * bar }}"""
    operator = '*'


class Div(BinExpr):
    """{{ foo / bar }}"""
    operator = '/'


class FloorDiv(BinExpr):
    """{{ foo // bar }}"""
    operator = '//'


class Add(BinExpr):
    """{{ foo + bar }}"""
    operator = '+'


class Sub(BinExpr):
    """{{ foo - bar }}"""
    operator = '-'


class Mod(BinExpr):
    """{{ foo % bar }}"""
    operator = '%'


class Pow(BinExpr):
    """{{ foo ** bar }}"""
    operator = '**'


class And(BinExpr):
    """{{ foo and bar }}"""
    operator = 'and'

    def as_const(self):
        return self.left.as_const() and self.right.as_const()


class Or(BinExpr):
    """{{ foo or bar }}"""
    operator = 'or'

    def as_const(self):
        return self.left.as_const() or self.right.as_const()


class Not(UnaryExpr):
    """{{ not foo }}"""
    operator = 'not'


class Neg(UnaryExpr):
    """{{ -foo }}"""
    operator = '-'


class Pos(UnaryExpr):
    """{{ +foo }}"""
    operator = '+'
