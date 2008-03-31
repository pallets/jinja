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
from jinja.datastructure import Deferred
from jinja.utils import deque


class BaseContext(object):

    def __init__(self, undefined_singleton, globals, initial):
        self._undefined_singleton = undefined_singleton
        self.current = current = {}
        self._stack = deque([current, initial, globals])
        self.globals = globals
        self.initial = initial

        self._push = self._stack.appendleft
        self._pop = self._stack.popleft

    def stack(self):
        return list(self._stack)[::-1]
    stack = property(stack)

    def pop(self):
        """Pop the last layer from the stack and return it."""
        rv = self._pop()
        self.current = self._stack[0]
        return rv

    def push(self, data=None):
        """
        Push one layer to the stack and return it. Layer must be
        a dict or omitted.
        """
        data = data or {}
        self._push(data)
        self.current = self._stack[0]
        return data

    def __getitem__(self, name):
        """
        Resolve one item. Restrict the access to internal variables
        such as ``'::cycle1'``. Resolve deferreds.
        """
        if not name.startswith('::'):
            for d in self._stack:
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
        """Set a variable in the outermost layer."""
        self.current[name] = value

    def __delitem__(self, name):
        """Delete a variable in the outermost layer."""
        if name in self.current:
            del self.current[name]

    def __contains__(self, name):
        """ Check if the context contains a given variable."""
        for layer in self._stack:
            if name in layer:
                return True
        return False
