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
from jinja2.runtime import subscribe, LoopContext


class ContextStack(object):
    """Simple compile time context implementation."""

    def __init__(self, initial=None):
        self.stack = [{}]
        if initial is not None:
            self.stack.insert(0, initial)

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        for level in reversed(self.stack):
            if key in level:
                return level[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.stack[-1][key] = value

    def blank(self):
        """Return a new context with nothing but the root scope."""
        return ContextStack(self.stack[0])


class Optimizer(NodeTransformer):

    def __init__(self, environment):
        self.environment = environment

    def visit_Block(self, node, context):
        return self.generic_visit(node, context.blank())

    def visit_Filter(self, node, context):
        """Try to evaluate filters if possible."""
        # XXX: nonconstant arguments?  not-called visitors?  generic visit!
        try:
            x = self.visit(node.node, context).as_const()
        except nodes.Impossible:
            return self.generic_visit(node, context)
        for filter in reversed(node.filters):
            # XXX: call filters with arguments
            x = self.environment.filters[filter.name](self.environment, x)
            # XXX: don't optimize context dependent filters
        return nodes.Const(x)

    def visit_For(self, node, context):
        """Loop unrolling for iterable constant values."""
        try:
            iterable = iter(self.visit(node.iter, context).as_const())
        except (nodes.Impossible, TypeError):
            return self.generic_visit(node, context)

        parent = context.get('loop')
        context.push()
        result = []
        iterated = False

        def assign(target, value):
            if isinstance(target, nodes.Name):
                context[target.name] = value
            elif isinstance(target, nodes.Tuple):
                try:
                    value = tuple(value)
                except TypeError:
                    raise nodes.Impossible()
                if len(target.items) != len(value):
                    raise nodes.Impossible()
                for name, val in zip(target.items, value):
                    assign(name, val)
            else:
                raise AssertionError('unexpected assignable node')

        # XXX: not covered cases:
        #       - item is accessed by dynamic part in the iteration
        try:
            try:
                for loop, item in LoopContext(iterable, parent):
                    context['loop'] = loop
                    assign(node.target, item)
                    result.extend(self.visit(n, context)
                                  for n in deepcopy(node.body))
                    iterated = True
                if not iterated and node.else_:
                    result.extend(self.visit(n, context)
                                  for n in deepcopy(node.else_))
            except nodes.Impossible:
                return node
        finally:
            context.pop()
        return result

    def visit_If(self, node, context):
        try:
            val = self.visit(node.test, context).as_const()
        except nodes.Impossible:
            return self.generic_visit(node, context)
        if val:
            return node.body
        return node.else_

    def visit_Name(self, node, context):
        if node.ctx == 'load':
            try:
                return nodes.Const(context[node.name], lineno=node.lineno)
            except KeyError:
                pass
        return node

    def visit_Assign(self, node, context):
        try:
            target = node.target = self.generic_visit(node.target, context)
            value = self.generic_visit(node.node, context).as_const()
        except nodes.Impossible:
            return node

        result = []
        lineno = node.lineno
        def walk(target, value):
            if isinstance(target, nodes.Name):
                const_value = nodes.Const(value, lineno=lineno)
                result.append(nodes.Assign(target, const_value, lineno=lineno))
                context[target.name] = value
            elif isinstance(target, nodes.Tuple):
                try:
                    value = tuple(value)
                except TypeError:
                    raise nodes.Impossible()
                if len(target.items) != len(value):
                    raise nodes.Impossible()
                for name, val in zip(target.items, value):
                    walk(name, val)
            else:
                raise AssertionError('unexpected assignable node')

        try:
            walk(target, value)
        except nodes.Impossible:
            return node
        return result

    def fold(self, node, context):
        """Do constant folding."""
        node = self.generic_visit(node, context)
        try:
            return nodes.Const(node.as_const(), lineno=node.lineno)
        except nodes.Impossible:
            return node
    visit_Add = visit_Sub = visit_Mul = visit_Div = visit_FloorDiv = \
    visit_Pow = visit_Mod = visit_And = visit_Or = visit_Pos = visit_Neg = \
    visit_Not = visit_Compare = fold

    def visit_Subscript(self, node, context):
        if node.ctx == 'load':
            try:
                item = self.visit(node.node, context).as_const()
                arg = self.visit(node.arg, context).as_const()
            except nodes.Impossible:
                return self.generic_visit(node, context)
            return nodes.Const(subscribe(item, arg, 'load'))
        return self.generic_visit(node, context)


def optimize(node, environment, context_hint=None):
    """The context hint can be used to perform an static optimization
    based on the context given."""
    optimizer = Optimizer(environment)
    return optimizer.visit(node, ContextStack(context_hint))
