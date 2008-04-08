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
from copy import deepcopy
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer


class Optimizer(NodeVisitor):

    def __init__(self, environment, context={}):
        self.environment = environment
        self.context = context

    def visit_Output(self, node):
        node.nodes = [self.visit(n) for n in node.nodes]
        return node

    def visit_Template(self, node):
        body = []
        for n in node.body:
            x = self.visit(n)
            if isinstance(x, list):
                body.extend(x)
            else:
                body.append(x)
        node.body = body
        return node

    def visit_Filter(self, node):
        """Try to evaluate filters if possible."""
        try:
            x = self.visit(node.node).as_const()
        except nodes.Impossible:
            return node
        for filter in reversed(node.filters):
            # XXX: call filters with arguments
            x = self.environment.filters[filter.name](self.environment, x)
            # XXX: don't optimize context dependent filters
        return nodes.Const(x)

    def visit_For(self, node):
        """Loop unrolling for constant values."""
        try:
            iter = self.visit(node.iter).as_const()
        except nodes.Impossible:
            return node
        result = []
        target = node.target.name
        for item in iter:
            # XXX: take care of variable scopes
            self.context[target] = item
            result.extend(self.visit(n) for n in deepcopy(node.body))
        return result

    def visit_Name(self, node):
        # XXX: take care of variable scopes!
        if node.name not in self.context:
            return node
        return nodes.Const(self.context[node.name])

    def generic_visit(self, node, *args, **kwargs):
        NodeVisitor.generic_visit(self, node, *args, **kwargs)
        return node


def optimize(node, environment):
    optimizer = Optimizer(environment)
    return optimizer.visit(node)
