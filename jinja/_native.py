# -*- coding: utf-8 -*-
"""
    jinja._native
    ~~~~~~~~~~~~~

    This module implements the native base classes in case of not
    having a jinja with the _speedups module compiled.

    Note that if you change semantics here you have to edit the
    _speedups.c file to in order to support those changes for jinja
    setups with enabled speedup module.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.datastructure import Deferred, Undefined


class BaseContext(object):

    def __init__(self, undefined_singleton, globals, initial):
        self._undefined_singleton = undefined_singleton
        self.current = current = {}
        self.stack = [globals, initial, current]
        self._push = self.stack.append
        self._pop = self.stack.pop
        self.globals = globals
        self.initial = initial

    def pop(self):
        """
        Pop the last layer from the stack and return it.
        """
        rv = self._pop()
        self.current = self.stack[-1]
        return rv

    def push(self, data=None):
        """
        Push one layer to the stack. Layer must be a dict or omitted.
        """
        data = data or {}
        self._push(data)
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
        return self._undefined_singleton

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
