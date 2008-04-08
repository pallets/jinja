# -*- coding: utf-8 -*-
"""
    jinja2.optimizer
    ~~~~~~~~~~~~~~~~

    This module tries to optimize template trees by:

        * eliminating constant nodes
        * evaluating filters and macros on constant nodes
        * unroll loops on constant values
        * replace variables which are already known (because they doesn't
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
from jinja2.runtime import subscribe


class Optimizer(NodeTransformer):

    def __init__(self, environment, context={}):
        self.environment = environment
        self.context = context

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

    def visit_Subscript(self, node):
        try:
            item = self.visit(node.node).as_const()
            arg = self.visit(node.arg).as_const()
        except nodes.Impossible:
            return node
        # XXX: what does the 3rd parameter mean?
        return nodes.Const(subscribe(item, arg, None))


def optimize(node, environment, context={}):
    optimizer = Optimizer(environment, context=context)
    return optimizer.visit(node)
