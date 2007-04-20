# -*- coding: utf-8 -*-
"""
    jinja._native
    ~~~~~~~~~~~~~

    This module implements the native base classes in case of not
    having a jinja with the _speedups module compiled.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.datastructure import Deferred, Undefined


class BaseContext(object):

    def __init__(self, silent, globals, initial):
        self.silent = silent
        self.current = current = {}
        self.stack = [globals, initial, current]
        self.globals = globals
        self.initial = initial

    def pop(self):
        """
        Pop the last layer from the stack and return it.
        """
        rv = self.stack.pop()
        self.current = self.stack[-1]
        return rv

    def push(self, data=None):
        """
        Push a new dict or empty layer to the stack and return that layer
        """
        data = data or {}
        self.stack.append(data)
        self.current = self.stack[-1]
        return data

    def __getitem__(self, name):
        """
        Resolve one item. Restrict the access to internal variables
        such as ``'::cycle1'``. Resolve deferreds.
        """
        if not name.startswith('::'):
            # because the stack is usually quite small we better
            # use [::-1] which is faster than reversed() in such
            # a situation.
            for d in self.stack[::-1]:
                if name in d:
                    rv = d[name]
                    if rv.__class__ is Deferred:
                        rv = rv(self, name)
                        # never touch the globals!
                        if d is self.globals:
                            self.initial[name] = rv
                        else:
                            d[name] = rv
                    return rv
        if self.silent:
            return Undefined
        raise TemplateRuntimeError('%r is not defined' % name)

    def __setitem__(self, name, value):
        """
        Set a variable in the outermost layer.
        """
        self.current[name] = value

    def __delitem__(self, name):
        """
        Delete an variable in the outermost layer.
        """
        if name in self.current:
            del self.current[name]

    def __contains__(self, name):
        """
        Check if the context contains a given variable.
        """
        for layer in self.stack:
            if name in layer:
                return True
        return False

    def __len__(self):
        """
        Size of the stack.
        """
        return len(self.stack)
