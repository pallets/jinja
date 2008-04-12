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
from jinja2 import nodes
from jinja2.visitor import NodeVisitor, NodeTransformer
from jinja2.runtime import subscribe, LoopContext


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
        return self.generic_visit(node, context.blank())

    def visit_Macro(self, node, context):
        context.push()
        try:
            return self.generic_visit(node, context)
        finally:
            context.pop()

    def visit_FilterBlock(self, node, context):
        """Try to filter a block at compile time."""
        node = self.generic_visit(node, context)
        context.push()

        # check if we can evaluate the wrapper body into a string
        # at compile time
        buffer = []
        for child in node.body:
            if not isinstance(child, nodes.Output):
                return node
            for item in child.optimized_nodes():
                if isinstance(item, nodes.Node):
                    return node
                buffer.append(item)

        # now check if we can evaluate the filter at compile time.
        try:
            data = node.filter.as_const(u''.join(buffer))
        except nodes.Impossible:
            return node

        context.pop()
        const = nodes.Const(data, lineno=node.lineno)
        return nodes.Output([const], lineno=node.lineno)

    def visit_For(self, node, context):
        """Loop unrolling for iterable constant values."""
        try:
            iterable = self.visit(node.iter, context).as_const()
            # we only unroll them if they have a length and are iterable
            iter(iterable)
            len(iterable)
            # we also don't want unrolling if macros are defined in it
            if node.find(nodes.Macro) is not None:
                raise TypeError()
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

        try:
            try:
                for loop, item in LoopContext(iterable, parent, True):
                    context['loop'] = loop.make_static()
                    assign(node.target, item)
                    result.extend(self.visit(n.copy(), context)
                                  for n in node.body)
                    iterated = True
                if not iterated and node.else_:
                    result.extend(self.visit(n.copy(), context)
                                  for n in node.else_)
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
                const = nodes.Const.from_untrusted(value, lineno=lineno)
                result.append(nodes.Assign(target, const, lineno=lineno))
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
            return nodes.Const.from_untrusted(node.as_const(),
                                              lineno=node.lineno,
                                              environment=self.environment)
        except nodes.Impossible:
            return node
    visit_Add = visit_Sub = visit_Mul = visit_Div = visit_FloorDiv = \
    visit_Pow = visit_Mod = visit_And = visit_Or = visit_Pos = visit_Neg = \
    visit_Not = visit_Compare = visit_Subscript = visit_Call = \
    visit_Filter = visit_Test = fold
    del fold
