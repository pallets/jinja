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
from compiler import ast
from copy import copy


def inc_lineno(offset, tree):
    """
    Increment the linenumbers of all nodes in tree with offset.
    """
    todo = [tree]
    while todo:
        node = todo.pop()
        if node.lineno:
            node.lineno += offset - 1
        else:
            node.lineno = offset
        todo.extend(node.getChildNodes())


def get_nodes(nodetype, tree, exclude_root=True):
    """
    Get all nodes from nodetype in the tree excluding the
    node passed if `exclude_root` is `True` (default).
    """
    if exclude_root:
        todo = tree.getChildNodes()
    else:
        todo = [tree]
    while todo:
        node = todo.pop()
        if node.__class__ is nodetype:
            yield node
        todo.extend(node.getChildNodes())


def get_nodes_parentinfo(nodetype, tree):
    """
    Like `get_nodes` but it yields tuples in the form ``(parent, node)``.
    If a node is a direct ancestor of `tree` parent will be `None`.

    Always excludes the root node.
    """
    todo = [tree]
    while todo:
        node = todo.pop()
        if node is tree:
            parent = None
        else:
            parent = node
        for child in node.getChildNodes():
            if child.__class__ is nodetype:
                yield parent, child
            todo.append(child)


class Node(ast.Node):
    """
    Jinja node.
    """

    def get_items(self):
        return []

    def getChildren(self):
        return self.get_items()

    def getChildNodes(self):
        return [x for x in self.get_items() if isinstance(x, ast.Node)]


class Text(Node):
    """
    Node that represents normal text.
    """

    def __init__(self, lineno, text):
        self.lineno = lineno
        self.text = text

    def get_items(self):
        return [self.text]

    def __repr__(self):
        return 'Text(%r)' % (self.text,)


class DynamicText(Node):
    """
    Note that represents normal text with string formattings.
    Those are used for texts that contain variables. The attribute
    `variables` contains a list of Print tags and nothing else.
    """

    def __init__(self, lineno, format_string, variables):
        self.lineno = lineno
        self.format_string = format_string
        self.variables = variables

    def get_items(self):
        return [self.format_string] + list(self.variables)

    def __repr__(self):
        return 'DynamicText(%r, %r)' % (
            self.format_string,
            self.variables
        )


class NodeList(list, Node):
    """
    A node that stores multiple childnodes.
    """

    def __init__(self, lineno, data=None):
        self.lineno = lineno
        list.__init__(self, data or ())

    getChildren = getChildNodes = lambda s: list(s) + s.get_items()

    def __repr__(self):
        return 'NodeList(%s)' % list.__repr__(self)


class Template(NodeList):
    """
    Node that represents a template.
    """

    def __init__(self, filename, body, extends):
        if body.__class__ is not NodeList:
            body = (body,)
        NodeList.__init__(self, 1, body)
        self.extends = extends
        self.filename = filename

    def get_items(self):
        return self.extends is not None and [self.extends] or []

    def __repr__(self):
        return 'Template(%r, %r, %s)' % (
            self.filename,
            self.extends,
            list.__repr__(self)
        )


class ForLoop(Node):
    """
    A node that represents a for loop
    """

    def __init__(self, lineno, item, seq, body, else_, recursive):
        self.lineno = lineno
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

    def __init__(self, lineno, tests, else_):
        self.lineno = lineno
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

    def __init__(self, lineno, seq):
        self.lineno = lineno
        self.seq = seq

    def get_items(self):
        return [self.seq]

    def __repr__(self):
        return 'Cycle(%r)' % (self.seq,)


class Print(Node):
    """
    A node that represents variable tags and print calls.
    """

    def __init__(self, lineno, variable):
        self.lineno = lineno
        self.variable = variable

    def get_items(self):
        return [self.variable]

    def __repr__(self):
        return 'Print(%r)' % (self.variable,)


class Macro(Node):
    """
    A node that represents a macro.
    """

    def __init__(self, lineno, name, arguments, body):
        self.lineno = lineno
        self.name = name
        self.arguments = arguments
        self.body = body

    def get_items(self):
        result = [self.name]
        if self.arguments:
            for item in self.arguments:
                result.extend(item)
        result.append(self.body)
        return result

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

    def __init__(self, lineno, expr, body):
        self.lineno = lineno
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
    Allow defining own variables.
    """

    def __init__(self, lineno, name, expr):
        self.lineno = lineno
        self.name = name
        self.expr = expr

    def get_items(self):
        return [self.name, self.expr]

    def __repr__(self):
        return 'Set(%r, %r)' % (
            self.name,
            self.expr
        )


class Filter(Node):
    """
    Node for filter sections.
    """

    def __init__(self, lineno, body, filters):
        self.lineno = lineno
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

    def __init__(self, lineno, name, body):
        self.lineno = lineno
        self.name = name
        self.body = body

    def replace(self, node):
        """
        Replace the current data with the data of another block node.
        """
        assert node.__class__ is Block
        self.__dict__.update(node.__dict__)

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


class Extends(Node):
    """
    A node that represents the extends tag.
    """

    def __init__(self, lineno, template):
        self.lineno = lineno
        self.template = template

    def get_items(self):
        return [self.template]

    def __repr__(self):
        return 'Extends(%r)' % self.template


class Include(Node):
    """
    A node that represents the include tag.
    """

    def __init__(self, lineno, template):
        self.lineno = lineno
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

    def __init__(self, lineno, singular, plural, indicator, replacements):
        self.lineno = lineno
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
