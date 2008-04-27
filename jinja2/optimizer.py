# -*- coding: utf-8 -*-
"""
    jinja2.optimizer
    ~~~~~~~~~~~~~~~~

    The jinja optimizer is currently trying to constant fold a few expressions
    and modify the AST in place so that it should be easier to evaluate it.

    Because the AST does not contain all the scoping information and the
    compiler has to find that out, we cannot do all the optimizations we
    want.  For example loop unrolling doesn't work because unrolled loops would
    have a different scoping.

    The solution would be a second syntax tree that has the scoping rules stored.

    :copyright: Copyright 2008 by Christoph Hack, Armin Ronacher.
    :license: GNU GPL.
"""
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.runtime import LoopContext, concat


def optimize(node, environment, context_hint=None):
    """The context hint can be used to perform an static optimization
    based on the context given."""
    optimizer = Optimizer(environment)
    return optimizer.visit(node, ContextStack(context_hint))


class ContextStack(object):
    """Simple compile time context implementation."""
    undefined = object()

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

    def undef(self, name):
        if name in self:
            self[name] = self.undefined

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        return True

    def __getitem__(self, key):
        for level in reversed(self.stack):
            if key in level:
                rv = level[key]
                if rv is self.undefined:
                    raise KeyError(key)
                return rv
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
        block_context = context.blank()
        for name in 'super', 'self':
            block_context.undef(name)
        return self.generic_visit(node, block_context)

    def visit_For(self, node, context):
        context.push()
        context.undef('loop')
        try:
            return self.generic_visit(node, context)
        finally:
            context.pop()

    def visit_Macro(self, node, context):
        context.push()
        for name in 'varargs', 'kwargs', 'caller':
            context.undef(name)
        try:
            return self.generic_visit(node, context)
        finally:
            context.pop()

    def visit_CallBlock(self, node, context):
        context.push()
        for name in 'varargs', 'kwargs':
            context.undef(name)
        try:
            return self.generic_visit(node, context)
        finally:
            context.pop()

    def visit_FilterBlock(self, node, context):
        """Try to filter a block at compile time."""
        context.push()
        try:
            return self.generic_visit(node, context)
        finally:
            context.pop()

    def visit_If(self, node, context):
        try:
            val = self.visit(node.test, context).as_const()
        except nodes.Impossible:
            return self.generic_visit(node, context)
        if val:
            body = node.body
        else:
            body = node.else_
        result = []
        for node in body:
            result.extend(self.visit_list(node, context))
        return result

    def visit_Name(self, node, context):
        if node.ctx != 'load':
            # something overwrote the variable, we can no longer use
            # the constant from the context
            context.undef(node.name)
            return node
        try:
            return nodes.Const.from_untrusted(context[node.name],
                                              lineno=node.lineno,
                                              environment=self.environment)
        except (KeyError, nodes.Impossible):
            return node

    def visit_Import(self, node, context):
        rv = self.generic_visit(node, context)
        context.undef(node.target)
        return rv

    def visit_FromImport(self, node, context):
        rv = self.generic_visit(node, context)
        for name in node.names:
            if isinstance(name, tuple):
                context.undef(name[1])
            else:
                context.undef(name)
        return rv

    def fold(self, node, context):
        """Do constant folding."""
        node = self.generic_visit(node, context)
        try:
            return nodes.Const.from_untrusted(node.as_const(),
                                              lineno=node.lineno,
                                              environment=self.environment)
        except nodes.Impossible:
            return node

    visit_Add = visit_Sub = visit_Mul = visit_Div = visit_FloorDiv = \
    visit_Pow = visit_Mod = visit_And = visit_Or = visit_Pos = visit_Neg = \
    visit_Not = visit_Compare = visit_Subscript = visit_Call = \
    visit_Filter = visit_Test = visit_CondExpr = fold
    del fold
