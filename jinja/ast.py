# -*- coding: utf-8 -*-
"""
    jinja.ast
    ~~~~~~~~~

    Advance Syntax Tree for jinja.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

class Node(object):
    """
    Baseclass of all nodes. For instance checking.
    """
    __slots__ = ()

    def __init__(self):
        raise TypeError('cannot create %r instances' %
                        self.__class__.__name__)


class Expression(list, Node):
    """
    Node that helds childnodes. Normally just used temporary.
    """
    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super(Expression, self).__init__(*args, **kwargs)

    def __repr__(self):
        return 'Expression(%s)' % list.__repr__(self)


class Comment(Node):
    """
    Node that helds a comment. We keep comments in the data
    if some translator wants to forward it into the generated
    code (for example the python translator).
    """
    __slots__ = ('pos', 'comment',)

    def __init__(self, pos, comment):
        self.pos = pos
        self.comment = comment

    def __repr__(self):
        return 'Comment(%r, %r)' % (self.pos, self.comment)


class Page(Node):
    """
    Node that helds all root nodes.
    """
    __slots__ = ('filename', 'nodes')

    def __init__(self, filename, nodes):
        self.filename = filename
        self.nodes = nodes

    def __repr__(self):
        return 'Page(%r, %r)' % (
            self.filename,
            self.nodes
        )


class Variable(Node):
    """
    Node for variables
    """
    __slots__ = ('pos', 'expression')

    def __init__(self, pos, expression):
        self.pos = pos
        self.expression = expression

    def __repr__(self):
        return 'Variable(%r)' % self.expression


class Data(Node):
    """
    Node for data outside of tags.
    """
    __slots__ = ('pos', 'data')

    def __init__(self, pos, data):
        self.pos = pos
        self.data = data

    def __repr__(self):
        return 'Data(%d, %r)' % (self.pos, self.data)


class Name(Node):
    """
    Node for names.
    """
    __slots__ = ('pos', 'data')

    def __init__(self, pos, data):
        self.pos = pos
        self.data = data

    def __repr__(self):
        return 'Name(%d, %r)' % (self.pos, self.data)
