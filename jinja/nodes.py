# -*- coding: utf-8 -*-
"""
    jinja.nodes
    ~~~~~~~~~~~

    Additional nodes for jinja. Look like nodes from the ast.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from compiler import ast
from compiler.misc import set_filename


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


class Node(ast.Node):
    """
    jinja node.
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


class NodeList(list, Node):
    """
    A node that stores multiple childnodes.
    """

    def __init__(self, lineno, data=None):
        self.lineno = lineno
        list.__init__(self, data or ())

    getChildren = getChildNodes = lambda s: list(s) + s.get_items()

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            list.__repr__(self)
        )


class Template(NodeList):
    """
    Node that represents a template.
    """

    def __init__(self, filename, body, blocks, extends):
        if body.__class__ is not NodeList:
            body = (body,)
        NodeList.__init__(self, 0, body)
        self.blocks = blocks
        self.extends = extends
        set_filename(filename, self)

    def get_items(self):
        result = self.blocks.values()
        if self.extends is not None:
            result.append(self.extends)
        return result


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
        for test in tests:
            result.extend(test)
        result.append(self._else)
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


class Filter(Node):
    """
    Node for filter sections.
    """

    def __init__(self, lineno, body, filters):
        self.lineno = lineno
        self.body = body
        self.filters = filters

    def get_items(self):
        return [self.body, self.filters]

    def __repr__(self):
        return 'Filter(%r)' % (
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
        return 'Include(%r)' % self.template
