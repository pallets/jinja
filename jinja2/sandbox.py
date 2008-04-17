# -*- coding: utf-8 -*-
"""
    jinja2.sandbox
    ~~~~~~~~~~~~~~

    Adds a sandbox layer to Jinja as it was the default behavior in the old
    Jinja 1 releases.  This sandbox is slightly different from Jinja 1 as the
    default behavior is easier to use.

    The behavior can be changed by subclassing the environment.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from types import FunctionType, MethodType
from jinja2.runtime import Undefined
from jinja2.environment import Environment


#: maximum number of items a range may produce
MAX_RANGE = 100000


def safe_range(*args):
    """A range that can't generate ranges with a length of more than
    MAX_RANGE items."""
    rng = xrange(*args)
    if len(rng) > MAX_RANGE:
        raise OverflowError('range too big')
    return rng


def unsafe(f):
    """Mark a function as unsafe."""
    f.unsafe_callable = True
    return f


class SandboxedEnvironment(Environment):
    """The sandboxed environment"""
    sandboxed = True

    def __init__(self, *args, **kwargs):
        Environment.__init__(self, *args, **kwargs)
        self.globals['range'] = safe_range

    def is_safe_attribute(self, obj, attr, value):
        """The sandboxed environment will call this method to check if the
        attribute of an object is safe to access.  Per default all attributes
        starting with an underscore are considered private as well as the
        special attributes of functions and methods.
        """
        if attr.startswith('_'):
            return False
        if isinstance(obj, FunctionType):
            return not attr.startswith('func_')
        if isinstance(obj, MethodType):
            return not attr.startswith('im_')
        return True

    def is_safe_callable(self, obj):
        """Check if an object is safely callable.  Per default a function is
        considered safe unless the `unsafe_callable` attribute exists and is
        truish.  Override this method to alter the behavior, but this won't
        affect the `unsafe` decorator from this module.
        """
        return not getattr(obj, 'unsafe_callable', False)

    def subscribe(self, obj, argument):
        """Subscribe an object from sandboxed code."""
        is_unsafe = False
        try:
            value = getattr(obj, str(argument))
        except (AttributeError, UnicodeError):
            pass
        else:
            if self.is_safe_attribute(obj, argument, value):
                return value
            is_unsafe = True
        try:
            return obj[argument]
        except (TypeError, LookupError):
            if is_unsafe:
                return self.undefined('access to attribute %r of %r object is'
                                      ' unsafe.' % (
                    argument,
                    obj.__class__.__name__
                ))
        return self.undefined(obj=obj, name=argument)

    def call(__self, __obj, *args, **kwargs):
        """Call an object from sandboxed code."""
        # the double prefixes are to avoid double keyword argument
        # errors when proxying the call.
        if not __self.is_safe_callable(__obj):
            raise TypeError('%r is not safely callable' % (__obj,))
        return __obj(*args, **kwargs)
