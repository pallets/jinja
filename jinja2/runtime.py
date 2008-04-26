# -*- coding: utf-8 -*-
"""
    jinja2.runtime
    ~~~~~~~~~~~~~~

    Runtime helpers.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
from types import FunctionType
from itertools import izip
from jinja2.utils import Markup, partial
from jinja2.exceptions import UndefinedError


# these variables are exported to the template runtime
__all__ = ['LoopContext', 'StaticLoopContext', 'TemplateContext',
           'Macro', 'Markup', 'missing', 'concat', 'izip']


# special singleton representing missing values for the runtime
missing = object()


# concatenate a list of strings and convert them to unicode.
concat = u''.join


class TemplateContext(object):
    """Holds the variables of the local template or of the global one.  It's
    not save to use this class outside of the compiled code.  For example
    update and other methods will not work as they seem (they don't update
    the exported variables for example).
    """

    def __init__(self, environment, parent, name, blocks):
        self.parent = parent
        self.vars = vars = {}
        self.environment = environment
        self.exported_vars = set()
        self.name = name

        # bind functions to the context of environment if required
        for name, obj in parent.iteritems():
            if type(obj) is FunctionType:
                if getattr(obj, 'contextfunction', 0):
                    vars[name] = partial(obj, self)
                elif getattr(obj, 'environmentfunction', 0):
                    vars[name] = partial(obj, environment)

        # create the initial mapping of blocks.  Whenever template inheritance
        # takes place the runtime will update this mapping with the new blocks
        # from the template.
        self.blocks = dict((k, [v]) for k, v in blocks.iteritems())

    def super(self, name, current):
        """Render a parent block."""
        last = None
        for block in self.blocks[name]:
            if block is current:
                break
            last = block
        if last is None:
            return self.environment.undefined('there is no parent block '
                                              'called %r.' % block)
        return SuperBlock(block, self, last)

    def get(self, name, default=None):
        """For dict compatibility"""
        try:
            return self[name]
        except KeyError:
            return default

    def update(self, mapping):
        """Update vars from a mapping but don't export them."""
        self.vars.update(mapping)

    def get_exported(self):
        """Get a new dict with the exported variables."""
        return dict((k, self.vars[k]) for k in self.exported_vars
                    if not k.startswith('__'))

    def get_root(self):
        """Return a new dict with all the non local variables."""
        return dict(self.parent)

    def get_all(self):
        """Return a copy of the complete context as dict."""
        return dict(self.parent, **self.vars)

    def __setitem__(self, key, value):
        self.vars[key] = value
        self.exported_vars.add(key)

    def __contains__(self, name):
        return name in self.vars or name in self.parent

    def __getitem__(self, key):
        if key in self.vars:
            return self.vars[key]
        try:
            return self.parent[key]
        except KeyError:
            return self.environment.undefined(name=key)

    def __repr__(self):
        return '<%s %s of %r>' % (
            self.__class__.__name__,
            repr(self.get_all()),
            self.name
        )


class SuperBlock(object):
    """When called this renders a parent block."""

    def __init__(self, name, context, render_func):
        self.name = name
        self._context = context
        self._render_func = render_func

    def __call__(self):
        return Markup(concat(self._render_func(self._context)))

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.name
        )


class LoopContextBase(object):
    """Helper for extended iteration."""

    def __init__(self, iterable, parent=None):
        self._iterable = iterable
        self._length = None
        self.index0 = 0
        self.parent = parent

    def cycle(self, *args):
        """A replacement for the old ``{% cycle %}`` tag."""
        if not args:
            raise TypeError('no items for cycling given')
        return args[self.index0 % len(args)]

    first = property(lambda x: x.index0 == 0)
    last = property(lambda x: x.revindex0 == 0)
    index = property(lambda x: x.index0 + 1)
    revindex = property(lambda x: x.length - x.index0)
    revindex0 = property(lambda x: x.length - x.index)

    def __len__(self):
        return self.length


class LoopContext(LoopContextBase):
    """A loop context for dynamic iteration."""

    def __init__(self, iterable, enforce_length=False):
        self._iterable = iterable
        self._next = iter(iterable).next
        self._length = None
        self.index0 = -1
        if enforce_length:
            len(self)

    def make_static(self):
        """Return a static loop context for the optimizer."""
        return StaticLoopContext(self.index0, self.length)

    def __iter__(self):
        return self

    def next(self):
        self.index0 += 1
        return self._next(), self

    @property
    def length(self):
        if self._length is None:
            try:
                length = len(self._iterable)
            except TypeError:
                self._iterable = tuple(self._iterable)
                self._next = iter(self._iterable).next
                length = len(tuple(self._iterable)) + self.index0 + 1
            self._length = length
        return self._length

    def __repr__(self):
        return 'LoopContext(%r)' % self.index0


class StaticLoopContext(LoopContextBase):
    """The static loop context is used in the optimizer to "freeze" the
    status of an iteration.  The only reason for this object is if the
    loop object is accessed in a non static way (eg: becomes part of a
    function call).
    """

    def __init__(self, index0, length):
        self.index0 = index0
        self.length = length

    def __repr__(self):
        """The repr is used by the optimizer to dump the object."""
        return 'StaticLoopContext(%r, %r)' % (
            self.index0,
            self.length
        )

    def make_static(self):
        return self


class Macro(object):
    """Wraps a macro."""

    def __init__(self, environment, func, name, arguments, defaults,
                 catch_kwargs, catch_varargs, caller):
        self._environment = environment
        self._func = func
        self.name = name
        self.arguments = arguments
        self.argument_count = len(arguments)
        self.defaults = defaults
        self.catch_kwargs = catch_kwargs
        self.catch_varargs = catch_varargs
        self.caller = caller

    def __call__(self, *args, **kwargs):
        self.argument_count = len(self.arguments)
        if not self.catch_varargs and len(args) > self.argument_count:
            raise TypeError('macro %r takes not more than %d argument(s)' %
                            (self.name, len(self.arguments)))
        arguments = []
        for idx, name in enumerate(self.arguments):
            try:
                value = args[idx]
            except IndexError:
                try:
                    value = kwargs.pop(name)
                except KeyError:
                    try:
                        value = self.defaults[idx - self.argument_count]
                    except IndexError:
                        value = self._environment.undefined(
                            'parameter %r was not provided' % name)
            arguments.append(value)

        # it's important that the order of these arguments does not change
        # if not also changed in the compiler's `function_scoping` method.
        # the order is caller, keyword arguments, positional arguments!
        if self.caller:
            caller = kwargs.pop('caller', None)
            if caller is None:
                caller = self._environment.undefined('No caller defined')
            arguments.append(caller)
        if self.catch_kwargs:
            arguments.append(kwargs)
        elif kwargs:
            raise TypeError('macro %r takes no keyword argument %r' %
                            (self.name, iter(kwargs).next()))
        if self.catch_varargs:
            arguments.append(args[self.argument_count:])
        return self._func(*arguments)

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.name is None and 'anonymous' or repr(self.name)
        )


def fail_with_undefined_error(self, *args, **kwargs):
    """Regular callback function for undefined objects that raises an
    `UndefinedError` on call.
    """
    if self._undefined_hint is None:
        if self._undefined_obj is None:
            hint = '%r is undefined' % self._undefined_name
        elif not isinstance(self._undefined_name, basestring):
            hint = '%r object has no element %r' % (
                self._undefined_obj.__class__.__name__,
                self._undefined_name
            )
        else:
            hint = '%r object has no attribute %r' % (
                self._undefined_obj.__class__.__name__,
                self._undefined_name
            )
    else:
        hint = self._undefined_hint
    raise UndefinedError(hint)


class Undefined(object):
    """The default undefined implementation.  This undefined implementation
    can be printed and iterated over, but every other access will raise a
    `NameError`.  Custom undefined classes must subclass this.
    """

    def __init__(self, hint=None, obj=None, name=None):
        self._undefined_hint = hint
        self._undefined_obj = obj
        self._undefined_name = name

    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
    __realdiv__ = __rrealdiv__ = __floordiv__ = __rfloordiv__ = \
    __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
    __getattr__ = __getitem__ = fail_with_undefined_error

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return 'Undefined'

    def __unicode__(self):
        return u''

    def __len__(self):
        return 0

    def __iter__(self):
        if 0:
            yield None

    def __nonzero__(self):
        return False


class DebugUndefined(Undefined):
    """An undefined that returns the debug info when printed."""

    def __unicode__(self):
        if self._undefined_hint is None:
            if self._undefined_obj is None:
                return u'{{ %s }}' % self._undefined_name
            return '{{ no such element: %s[%r] }}' % (
                self._undefined_obj.__class__.__name__,
                self._undefined_name
            )
        return u'{{ undefined value printed: %s }}' % self._undefined_hint


class StrictUndefined(Undefined):
    """An undefined that barks on print and iteration as well as boolean
    tests.  In other words: you can do nothing with it except checking if it's
    defined using the `defined` test.
    """

    __iter__ = __unicode__ = __len__ = __nonzero__ = fail_with_undefined_error
