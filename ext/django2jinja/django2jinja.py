# -*- coding: utf-8 -*-
"""
    Django to Jinja
    ~~~~~~~~~~~~~~~

    Helper module that can convert django templates into Jinja2 templates.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import sys
import re
from jinja2.defaults import *
from django.conf import settings
from django.template import defaulttags as core_tags, loader, TextNode, \
     FilterExpression, libraries, Variable, loader_tags
from django.template.debug import DebugVariableNode as VariableNode
from StringIO import StringIO


node_handlers = {}
_resolved_filters = {}


_newline_re = re.compile(r'(?:\r\n|\r|\n)')


def node(cls):
    def proxy(f):
        node_handlers[cls] = f
        return f
    return proxy


def translate_variable_name(var):
    if var == 'forloop':
        return 'loop'
    return var


def get_filter_name(filter):
    if filter not in _resolved_filters:
        for library in libraries.values():
            for key, value in library.filters.iteritems():
                _resolved_filters[value] = key
    return _resolved_filters.get(filter, None)


class Writer(object):

    def __init__(self, stream=None,
                 block_start_string=BLOCK_START_STRING,
                 block_end_string=BLOCK_END_STRING,
                 variable_start_string=VARIABLE_START_STRING,
                 variable_end_string=VARIABLE_END_STRING,
                 comment_start_string=COMMENT_START_STRING,
                 comment_end_string=COMMENT_END_STRING):
        if stream is None:
            stream = sys.stdout
        self.stream = stream
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string

    def write(self, s):
        self.stream.write(s)

    def print_expr(self, expr):
        self.start_variable()
        self.write(expr)
        self.end_variable()

    def start_variable(self):
        self.write(self.variable_start_string + ' ')

    def end_variable(self):
        self.write(' ' + self.variable_end_string)

    def start_block(self):
        self.write(self.block_start_string + ' ')

    def end_block(self):
        self.write(' ' + self.block_end_string)

    def tag(self, name):
        self.start_block()
        self.write(name)
        self.end_block()

    def variable(self, name):
        self.write(translate_variable_name(name))

    def literal(self, value):
        value = repr(value)
        if value[:2] in ('u"', "u'"):
            value = value[1:]
        self.write(value)

    def warn(self, message, node=None):
        if node is not None and hasattr(node, 'source'):
            message = '[%s:%d] %s' % (
                node.source[0].name.replace('&lt;', '<') \
                                   .replace('&gt;', '>'),
                len(_newline_re.findall(node.source[0].source
                                        [:node.source[1][0]])),
                message
            )
        print >> sys.stderr, message

    def node(self, node):
        for cls, handler in node_handlers.iteritems():
            if type(node) is cls:
                handler(node, self)
                break
        else:
            self.warn('Untranslatable node %s.%s found' % (
                node.__module__,
                node.__class__.__name__
            ), node)

    def body(self, nodes):
        for node in nodes:
            self.node(node)


@node(TextNode)
def text_node(node, writer):
    writer.write(node.s)


@node(Variable)
def variable(node, writer):
    if node.literal is not None:
        writer.literal(node.literal)
    else:
        writer.variable(node.var)


@node(VariableNode)
def variable_node(node, writer):
    writer.start_variable()
    writer.node(node.filter_expression)
    writer.end_variable()


@node(FilterExpression)
def filter_expression(node, writer):
    writer.node(node.var)
    for filter, args in node.filters:
        name = get_filter_name(filter)
        if name is None:
            writer.warn('Could not find filter %s' % name, node)
        writer.write('|%s' % name)
        if args:
            writer.write('(')
            for idx, (is_var, value) in enumerate(args):
                if idx:
                    writer.write(', ')
                if is_var:
                    writer.node(value)
                else:
                    writer.literal(value)
            writer.write(')')


@node(core_tags.CommentNode)
def comment_tag(node, writer):
    pass


@node(core_tags.DebugNode)
def comment_tag(node, writer):
    writer.warn('Debug tag detected.  Make sure to add a global function '
                'called debug to the namespace.', node=node)
    writer.print_expr('debug()')


@node(core_tags.ForNode)
def for_loop(node, writer):
    writer.start_block()
    writer.write('for ')
    for idx, var in enumerate(node.loopvars):
        if idx:
            writer.write(', ')
        writer.variable(var)
    writer.write(' in ')
    if node.is_reversed:
        writer.write('(')
    writer.node(node.sequence)
    if node.is_reversed:
        writer.write(')|reverse')
    writer.end_block()
    writer.body(node.nodelist_loop)
    writer.tag('endfor')


@node(core_tags.IfNode)
def if_condition(node, writer):
    writer.start_block()
    writer.write('if ')
    join_with = core_tags.IfNode.LinkTypes.or_ and 'or' or 'and'
    for idx, (ifnot, expr) in enumerate(node.bool_exprs):
        if idx:
            writer.write(' %s ' % join_with)
        if ifnot:
            writer.write('not ')
        writer.node(expr)
    writer.end_block()
    writer.body(node.nodelist_true)
    if node.nodelist_false:
        writer.tag('else')
        writer.body(node.nodelist_false)
    writer.tag('endif')


@node(core_tags.IfEqualNode)
def if_equal(node, writer):
    writer.start_block()
    writer.write('if ')
    writer.node(node.var1)
    writer.write(' == ')
    writer.node(node.var2)
    writer.end_block()
    writer.body(node.nodelist_true)
    if node.nodelist_false:
        writer.tag('else')
        writer.body(node.nodelist_false)
    writer.tag('endif')


@node(loader_tags.BlockNode)
def block(node, writer):
    writer.tag('block ' + node.name.replace('-', '_'))
    node = node
    while node.parent is not None:
        node = node.parent
    writer.body(node.nodelist)
    writer.tag('endblock')


@node(loader_tags.ExtendsNode)
def extends(node, writer):
    writer.start_block()
    writer.write('extends ')
    if node.parent_name_expr:
        writer.node(node.parent_name_expr)
    else:
        writer.literal(node.parent_name)
    writer.end_block()
    writer.body(node.nodelist)


if __name__ == '__main__':
    settings.configure(TEMPLATE_DEBUG=True, TEMPLATE_DIRS=['templates'])
    Writer().body(loader.get_template('index.html'))
