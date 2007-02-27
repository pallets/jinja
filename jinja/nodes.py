# -*- coding: utf-8 -*-
"""
    jinja.nodes
    ~~~~~~~~~~~

    Additional nodes for jinja. Look like nodes from the ast.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from compiler.ast import Node


class Text(Node):
    """
    Node that represents normal text.
    """

    def __init__(self, pos, text):
        self.pos = pos
        self.text = text

    def __repr__(self):
        return 'Text(%r)' % (self.text,)


class NodeList(list, Node):
    """
    A node that stores multiple childnodes.
    """

    def __init__(self, pos, data=None):
        self.pos = pos
        list.__init__(self, data or ())

    def __repr__(self):
        return 'NodeList(%s)' % list.__repr__(self)


class ForLoop(Node):
    """
    A node that represents a for loop
    """

    def __init__(self, pos, item, seq, body, else_):
        self.pos = pos
        self.item = item
        self.seq = seq
        self.body = body
        self.else_ = else_

    def __repr__(self):
        return 'ForLoop(%r, %r, %r, %r)' % (
            self.item,
            self.seq,
            self.body,
            self.else_
        )


class IfCondition(Node):
    """
    A node that represents an if condition.
    """

    def __init__(self, pos, test, body, else_):
        self.pos = pos
        self.test = test
        self.body = body
        self.else_ = else_

    def __repr__(self):
        return 'IfCondition(%r, %r, %r)' % (
            self.test,
            self.body,
            self.else_
        )


class Cycle(Node):
    """
    A node that represents the cycle statement.
    """

    def __init__(self, pos, seq):
        self.pos = pos
        self.seq = seq

    def __repr__(self):
        return 'Cycle(%r)' % (self.seq,)


class Print(Node):
    """
    A node that represents variable tags and print calls
    """

    def __init__(self, pos, variable):
        self.pos = pos
        self.variable = variable

    def __repr__(self):
        return 'Print(%r)' % (self.variable,)
