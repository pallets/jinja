# -*- coding: utf-8 -*-
"""
    jinja2.optimizer
    ~~~~~~~~~~~~~~~~

    This module tries to optimize template trees by:

        * eliminating constant nodes
        * evaluating filters and macros on constant nodes
        * unroll loops on constant values
        * replace variables which are already known (because the doesn't
          change often and you want to prerender a template) with constants

    After the optimation you will get a new, simplier template which can
    be saved again for later rendering. But even if you don't want to
    prerender a template, this module might speed up your templates a bit
    if you are using a lot of constants.

    :copyright: Copyright 2008 by Christoph Hack.
    :license: GNU GPL.
"""
from copy import copy
from random import randrange
from operator import xor
from cStringIO import StringIO
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.exceptions import TemplateAssertionError


class Optimizer(NodeVisitor):

    def __init__(self, environment, context={}):
        self.environment = environment
        self.context = context

    def visit_Output(self, node):
        node.nodes = [self.visit(n) for n in node.nodes]
        return node

    def visit_Filter(self, node):
        """Try to evaluate filters if possible."""
        value = self.visit(node.node)
        if isinstance(value, nodes.Const):
            x = value.value
            for filter in reversed(node.filters):
                # XXX: call filters with arguments
                x = self.environment.filters[filter.name](self.environment, x)
                # XXX: don't optimize context dependent filters
            return nodes.Const(x)
        return node

    def generic_visit(self, node, *args, **kwargs):
        NodeVisitor.generic_visit(self, node, *args, **kwargs)
        return node


def optimize(ast, env, clone=True):
    optimizer = Optimizer(env)
    if clone:
        ast = copy(ast)
    return optimizer.visit(ast)
