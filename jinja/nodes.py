# -*- coding: utf-8 -*-
"""
    jinja.nodes
    ~~~~~~~~~~~

    This module implements additional nodes derived from the ast base node.

    It also provides some node tree helper functions like `in_lineno` and
    `get_nodes` used by the parser and translator in order to normalize
    python and jinja nodes.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from itertools import chain
from copy import copy


def get_nodes(nodetype, tree, exclude_root=True):
    """
    Get all nodes from nodetype in the tree excluding the
    node passed if `exclude_root` is `True` (default).
    """
    if exclude_root:
        todo = tree.get_child_nodes()
    else:
        todo = [tree]
    while todo:
        node = todo.pop()
        if node.__class__ is nodetype:
            yield node
        todo.extend(node.get_child_nodes())


class NotPossible(NotImplementedError):
    """
    If a given node cannot do something.
    """


class Node(object):
    """
    Jinja node.
    """

    def __init__(self, lineno=None, filename=None):
        self.lineno = lineno
        self.filename = filename

    def get_items(self):
        return []

    def get_child_nodes(self):
        return [x for x in self.get_items() if isinstance(x, Node)]

    def allows_assignments(self):
        return False

    def __repr__(self):
        return 'Node()'


class Text(Node):
    """
    Node that represents normal text.
    """

    def __init__(self, text, variables, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.text = text
        self.variables = variables

    def get_items(self):
        return [self.text] + list(self.variables)

    def __repr__(self):
        return 'Text(%r, %r)' % (
            self.text,
            self.variables
        )


class NodeList(list, Node):
    """
    A node that stores multiple childnodes.
    """

    def __init__(self, data, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        list.__init__(self, data)

    def get_items(self):
        return list(self)

    def __repr__(self):
        return 'NodeList(%s)' % list.__repr__(self)


class Template(Node):
    """
    Node that represents a template.
    """

    def __init__(self, extends, body, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.extends = extends
        self.body = body

    def get_items(self):
        return [self.extends, self.body]

    def __repr__(self):
        return 'Template(%r, %r)' % (
            self.extends,
            self.body
        )


class ForLoop(Node):
    """
    A node that represents a for loop
    """

    def __init__(self, item, seq, body, else_, recursive, lineno=None,
                 filename=None):
        Node.__init__(self, lineno, filename)
        self.item = item
        self.seq = seq
        self.body = body
        self.else_ = else_
        self.recursive = recursive

    def get_items(self):
        return [self.item, self.seq, self.body, self.else_, self.recursive]

    def __repr__(self):
        return 'ForLoop(%r, %r, %r, %r, %r)' % (
            self.item,
            self.seq,
            self.body,
            self.else_,
            self.recursive
        )


class IfCondition(Node):
    """
    A node that represents an if condition.
    """

    def __init__(self, tests, else_, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.tests = tests
        self.else_ = else_

    def get_items(self):
        result = []
        for test in self.tests:
            result.extend(test)
        result.append(self.else_)
        return result

    def __repr__(self):
        return 'IfCondition(%r, %r)' % (
            self.tests,
            self.else_
        )


class Cycle(Node):
    """
    A node that represents the cycle statement.
    """

    def __init__(self, seq, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.seq = seq

    def get_items(self):
        return [self.seq]

    def __repr__(self):
        return 'Cycle(%r)' % (self.seq,)


class Print(Node):
    """
    A node that represents variable tags and print calls.
    """

    def __init__(self, expr, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.expr = expr

    def get_items(self):
        return [self.expr]

    def __repr__(self):
        return 'Print(%r)' % (self.expr,)


class Macro(Node):
    """
    A node that represents a macro.
    """

    def __init__(self, name, arguments, body, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.name = name
        self.arguments = arguments
        self.body = body

    def get_items(self):
        return [self.name] + list(chain(*self.arguments)) + [self.body]

    def __repr__(self):
        return 'Macro(%r, %r, %r)' % (
            self.name,
            self.arguments,
            self.body
        )


class Call(Node):
    """
    A node that represents am extended macro call.
    """

    def __init__(self, expr, body, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.expr = expr
        self.body = body

    def get_items(self):
        return [self.expr, self.body]

    def __repr__(self):
        return 'Call(%r, %r)' % (
            self.expr,
            self.body
        )


class Set(Node):
    """
    Allows defining own variables.
    """

    def __init__(self, name, expr, scope_local, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.name = name
        self.expr = expr
        self.scope_local = scope_local

    def get_items(self):
        return [self.name, self.expr, self.scope_local]

    def __repr__(self):
        return 'Set(%r, %r, %r)' % (
            self.name,
            self.expr,
            self.scope_local
        )


class Filter(Node):
    """
    Node for filter sections.
    """

    def __init__(self, body, filters, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.body = body
        self.filters = filters

    def get_items(self):
        return [self.body] + list(self.filters)

    def __repr__(self):
        return 'Filter(%r, %r)' % (
            self.body,
            self.filters
        )


class Block(Node):
    """
    A node that represents a block.
    """

    def __init__(self, name, body, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.name = name
        self.body = body

    def replace(self, node):
        """
        Replace the current data with the copied data of another block
        node.
        """
        assert node.__class__ is Block
        self.lineno = node.lineno
        self.filename = node.filename
        self.name = node.name
        self.body = copy(node.body)

    def clone(self):
        """
        Create an independent clone of this node.
        """
        return copy(self)

    def get_items(self):
        return [self.name, self.body]

    def __repr__(self):
        return 'Block(%r, %r)' % (
            self.name,
            self.body
        )


class Include(Node):
    """
    A node that represents the include tag.
    """

    def __init__(self, template, lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.template = template

    def get_items(self):
        return [self.template]

    def __repr__(self):
        return 'Include(%r)' % (
            self.template
        )


class Trans(Node):
    """
    A node for translatable sections.
    """

    def __init__(self, singular, plural, indicator, replacements,
                 lineno=None, filename=None):
        Node.__init__(self, lineno, filename)
        self.singular = singular
        self.plural = plural
        self.indicator = indicator
        self.replacements = replacements

    def get_items(self):
        rv = [self.singular, self.plural, self.indicator]
        if self.replacements:
            rv.extend(self.replacements.values())
            rv.extend(self.replacements.keys())
        return rv

    def __repr__(self):
        return 'Trans(%r, %r, %r, %r)' % (
            self.singular,
            self.plural,
            self.indicator,
            self.replacements
        )


class Expression(Node):
    """
    Baseclass for all expressions.
    """


class BinaryExpression(Expression):
    """
    Baseclass for all binary expressions.
    """

    def __init__(self, left, right, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.left = left
        self.right = right

    def get_items(self):
        return [self.left, self.right]

    def __repr__(self):
        return '%s(%r, %r)' % (
            self.__class__.__name__,
            self.left,
            self.right
        )


class UnaryExpression(Expression):
    """
    Baseclass for all unary expressions.
    """

    def __init__(self, node, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.node = node

    def get_items(self):
        return [self.node]

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self.node
        )


class ConstantExpression(Expression):
    """
    any constat such as {{ "foo" }}
    """

    def __init__(self, value, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.value = value

    def get_items(self):
        return [self.value]

    def __repr__(self):
        return 'ConstantExpression(%r)' % (self.value,)


class UndefinedExpression(Expression):
    """
    represents the special 'undefined' value.
    """

    def __repr__(self):
        return 'UndefinedExpression()'


class RegexExpression(Expression):
    """
    represents the regular expression literal.
    """

    def __init__(self, value, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.value = value

    def get_items(self):
        return [self.value]

    def __repr__(self):
        return 'RegexExpression(%r)' % (self.value,)


class NameExpression(Expression):
    """
    any name such as {{ foo }}
    """

    def __init__(self, name, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.name = name

    def get_items(self):
        return [self.name]

    def allows_assignments(self):
        return self.name != '_'

    def __repr__(self):
        return 'NameExpression(%r)' % self.name


class ListExpression(Expression):
    """
    any list literal such as {{ [1, 2, 3] }}
    """

    def __init__(self, items, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.items = items

    def get_items(self):
        return list(self.items)

    def __repr__(self):
        return 'ListExpression(%r)' % (self.items,)


class DictExpression(Expression):
    """
    any dict literal such as {{ {1: 2, 3: 4} }}
    """

    def __init__(self, items, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.items = items

    def get_items(self):
        return list(chain(*self.items))

    def __repr__(self):
        return 'DictExpression(%r)' % (self.items,)


class SetExpression(Expression):
    """
    any set literal such as {{ @(1, 2, 3) }}
    """

    def __init__(self, items, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.items = items

    def get_items(self):
        return self.items[:]

    def __repr__(self):
        return 'SetExpression(%r)' % (self.items,)


class ConditionalExpression(Expression):
    """
    {{ foo if bar else baz }}
    """

    def __init__(self, test, expr1, expr2, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.test = test
        self.expr1 = expr1
        self.expr2 = expr2

    def get_items(self):
        return [self.test, self.expr1, self.expr2]

    def __repr__(self):
        return 'ConstantExpression(%r, %r, %r)' % (
            self.test,
            self.expr1,
            self.expr2
        )


class FilterExpression(Expression):
    """
    {{ foo|bar|baz }}
    """

    def __init__(self, node, filters, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.node = node
        self.filters = filters

    def get_items(self):
        result = [self.node]
        for filter, args in self.filters:
            result.append(filter)
            result.extend(args)
        return result

    def __repr__(self):
        return 'FilterExpression(%r, %r)' % (
            self.node,
            self.filters
        )


class TestExpression(Expression):
    """
    {{ foo is lower }}
    """

    def __init__(self, node, name, args, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.node = node
        self.name = name
        self.args = args

    def get_items(self):
        return [self.node, self.name] + list(self.args)

    def __repr__(self):
        return 'TestExpression(%r, %r, %r)' % (
            self.node,
            self.name,
            self.args
        )


class CallExpression(Expression):
    """
    {{ foo(bar) }}
    """

    def __init__(self, node, args, kwargs, dyn_args, dyn_kwargs,
                 lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.node = node
        self.args = args
        self.kwargs = kwargs
        self.dyn_args = dyn_args
        self.dyn_kwargs = dyn_kwargs

    def get_items(self):
        return [self.node, self.args, self.kwargs, self.dyn_args,
                self.dyn_kwargs]

    def __repr__(self):
        return 'CallExpression(%r, %r, %r, %r, %r)' % (
            self.node,
            self.args,
            self.kwargs,
            self.dyn_args,
            self.dyn_kwargs
        )


class SubscriptExpression(Expression):
    """
    {{ foo.bar }} and {{ foo['bar'] }} etc.
    """

    def __init__(self, node, arg, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.node = node
        self.arg = arg

    def get_items(self):
        return [self.node, self.arg]

    def __repr__(self):
        return 'SubscriptExpression(%r, %r)' % (
            self.node,
            self.arg
        )


class SliceExpression(Expression):
    """
    1:2:3 etc.
    """

    def __init__(self, start, stop, step, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.start = start
        self.stop = stop
        self.step = step

    def get_items(self):
        return [self.start, self.stop, self.step]

    def __repr__(self):
        return 'SliceExpression(%r, %r, %r)' % (
            self.start,
            self.stop,
            self.step
        )


class TupleExpression(Expression):
    """
    For loop unpacking and some other things like multiple arguments
    for subscripts.
    """

    def __init__(self, items, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.items = items

    def get_items(self):
        return list(self.items)

    def allows_assignments(self):
        for item in self.items:
            if not item.allows_assignments():
                return False
        return True

    def __repr__(self):
        return 'TupleExpression(%r)' % (self.items,)


class ConcatExpression(Expression):
    """
    For {{ foo ~ bar }}. Because of various reasons (especially because
    unicode conversion takes place for the left and right expression and
    is better optimized that way)
    """

    def __init__(self, args, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.args = args

    def get_items(self):
        return list(self.args)

    def __repr__(self):
        return 'ConcatExpression(%r)' % (self.items,)


class CompareExpression(Expression):
    """
    {{ foo == bar }}, {{ foo >= bar }} etc.
    """

    def __init__(self, expr, ops, lineno=None, filename=None):
        Expression.__init__(self, lineno, filename)
        self.expr = expr
        self.ops = ops

    def get_items(self):
        return [self.expr] + list(chain(*self.ops))

    def __repr__(self):
        return 'CompareExpression(%r, %r)' % (
            self.expr,
            self.ops
        )


class MulExpression(BinaryExpression):
    """
    {{ foo * bar }}
    """


class DivExpression(BinaryExpression):
    """
    {{ foo / bar }}
    """


class FloorDivExpression(BinaryExpression):
    """
    {{ foo // bar }}
    """


class AddExpression(BinaryExpression):
    """
    {{ foo + bar }}
    """


class SubExpression(BinaryExpression):
    """
    {{ foo - bar }}
    """


class ModExpression(BinaryExpression):
    """
    {{ foo % bar }}
    """


class PowExpression(BinaryExpression):
    """
    {{ foo ** bar }}
    """


class AndExpression(BinaryExpression):
    """
    {{ foo and bar }}
    """


class OrExpression(BinaryExpression):
    """
    {{ foo or bar }}
    """


class NotExpression(UnaryExpression):
    """
    {{ not foo }}
    """


class NegExpression(UnaryExpression):
    """
    {{ -foo }}
    """


class PosExpression(UnaryExpression):
    """
    {{ +foo }}
    """
