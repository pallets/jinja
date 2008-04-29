# -*- coding: utf-8 -*-
"""
    jinja2.runtime
    ~~~~~~~~~~~~~~

    Runtime helpers.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
import sys
from types import FunctionType
from itertools import chain, imap
from jinja2.utils import Markup, partial, soft_unicode, escape
from jinja2.exceptions import UndefinedError, TemplateRuntimeError


# these variables are exported to the template runtime
__all__ = ['LoopContext', 'TemplateContext', 'TemplateReference', 'Macro',
           'TemplateRuntimeError', 'Markup', 'missing', 'concat', 'escape',
           'markup_join', 'unicode_join']


# special singleton representing missing values for the runtime
missing = type('MissingType', (), {'__repr__': lambda x: 'missing'})()


# concatenate a list of strings and convert them to unicode.
# unfortunately there is a bug in python 2.4 and lower that causes
# unicode.join trash the traceback.
try:
    def _test_gen_bug():
        raise TypeError(_test_gen_bug)
        yield None
    u''.join(_test_gen_bug())
except TypeError, e:
    if e.args and e.args[0] is _test_gen_bug:
        concat = u''.join
    else:
        def concat(gen):
            try:
                return u''.join(list(gen))
            except:
                exc_type, exc_value, tb = sys.exc_info()
                raise exc_type, exc_value, tb.tb_next
del _test_gen_bug


def markup_join(*args):
    """Concatenation that escapes if necessary and converts to unicode."""
    buf = []
    iterator = imap(soft_unicode, args)
    for arg in iterator:
        buf.append(arg)
        if hasattr(arg, '__html__'):
            return Markup(u'').join(chain(buf, iterator))
    return concat(buf)


def unicode_join(*args):
    """Simple args to unicode conversion and concatenation."""
    return concat(imap(unicode, args))


class TemplateContext(object):
    """Holds the variables of the local template or of the global one.  It's
    not save to use this class outside of the compiled code.  For example
    update and other methods will not work as they seem (they don't update
    the exported variables for example).

    The context is immutable.  Modifications on `parent` must not happen and
    modifications on `vars` are allowed from generated template code.  However
    functions that are passed the template context may not modify the context
    in any way.
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
        try:
            blocks = self.blocks[name]
            pos = blocks.index(current) - 1
            if pos < 0:
                raise IndexError()
        except LookupError:
            return self.environment.undefined('there is no parent block '
                                              'called %r.' % name)
        wrap = self.environment.autoescape and Markup or (lambda x: x)
        render = lambda: wrap(concat(blocks[pos](self)))
        render.__name__ = render.name = name
        return render

    def get(self, key, default=None):
        """For dict compatibility"""
        if key in self.vars:
            return self.vars[key]
        if key in self.parent:
            return self.parent[key]
        return default

    def get_exported(self):
        """Get a new dict with the exported variables."""
        return dict((k, self.vars[k]) for k in self.exported_vars)

    def get_root(self):
        """Return a new dict with all the non local variables."""
        return dict(self.parent)

    def get_all(self):
        """Return a copy of the complete context as dict."""
        return dict(self.parent, **self.vars)

    def clone(self):
        """Return a copy of the context without the locals."""
        return self.__class__(self.environment, self.parent,
                              self.name, self.blocks)

    def __contains__(self, name):
        return name in self.vars or name in self.parent

    def __getitem__(self, key):
        if key in self.vars:
            return self.vars[key]
        if key in self.parent:
            return self.parent[key]
        return self.environment.undefined(name=key)

    def __repr__(self):
        return '<%s %s of %r>' % (
            self.__class__.__name__,
            repr(self.get_all()),
            self.name
        )


class TemplateReference(object):
    """The `self` in templates."""

    def __init__(self, context):
        self.__context = context

    def __getitem__(self, name):
        func = self.__context.blocks[name][-1]
        wrap = self.__context.environment.autoescape and \
               Markup or (lambda x: x)
        render = lambda: wrap(concat(func(self.__context)))
        render.__name__ = render.name = name
        return render

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._context.name
        )


class LoopContext(object):
    """A loop context for dynamic iteration."""

    def __init__(self, iterable, enforce_length=False):
        self._iterable = iterable
        self._next = iter(iterable).next
        self._length = None
        self.index0 = -1
        if enforce_length:
            len(self)

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
        return '<%s %r/%r>' % (
            self.__class__.__name__,
            self.index,
            self.length
        )


class Macro(object):
    """Wraps a macro."""

    def __init__(self, environment, func, name, arguments, defaults,
                 catch_kwargs, catch_varargs, caller):
        self._environment = environment
        self._func = func
        self._argument_count = len(arguments)
        self.name = name
        self.arguments = arguments
        self.defaults = defaults
        self.catch_kwargs = catch_kwargs
        self.catch_varargs = catch_varargs
        self.caller = caller

    def __call__(self, *args, **kwargs):
        if not self.catch_varargs and len(args) > self._argument_count:
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
                        value = self.defaults[idx - self._argument_count]
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
            arguments.append(args[self._argument_count:])
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
    """The default undefined type.  This undefined type can be printed and
    iterated over, but every other access will raise an :exc:`UndefinedError`:

    >>> foo = Undefined(name='foo')
    >>> str(foo)
    ''
    >>> not foo
    True
    >>> foo + 42
    Traceback (most recent call last):
      ...
    jinja2.exceptions.UndefinedError: 'foo' is undefined
    """
    __slots__ = ('_undefined_hint', '_undefined_obj', '_undefined_name')

    def __init__(self, hint=None, obj=None, name=None):
        self._undefined_hint = hint
        self._undefined_obj = obj
        self._undefined_name = name

    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
    __realdiv__ = __rrealdiv__ = __floordiv__ = __rfloordiv__ = \
    __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
    __getattr__ = __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = \
        fail_with_undefined_error

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
    """An undefined that returns the debug info when printed.

    >>> foo = DebugUndefined(name='foo')
    >>> str(foo)
    '{{ foo }}'
    >>> not foo
    True
    >>> foo + 42
    Traceback (most recent call last):
      ...
    jinja2.exceptions.UndefinedError: 'foo' is undefined
    """
    __slots__ = ()

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
    tests and all kinds of comparisons.  In other words: you can do nothing
    with it except checking if it's defined using the `defined` test.

    >>> foo = StrictUndefined(name='foo')
    >>> str(foo)
    Traceback (most recent call last):
      ...
    jinja2.exceptions.UndefinedError: 'foo' is undefined
    >>> not foo
    Traceback (most recent call last):
      ...
    jinja2.exceptions.UndefinedError: 'foo' is undefined
    >>> foo + 42
    Traceback (most recent call last):
      ...
    jinja2.exceptions.UndefinedError: 'foo' is undefined
    """
    __slots__ = ()
    __iter__ = __unicode__ = __len__ = __nonzero__ = __eq__ = __ne__ = \
        fail_with_undefined_error


# remove remaining slots attributes, after the metaclass did the magic they
# are unneeded and irritating as they contain wrong data for the subclasses.
del Undefined.__slots__, DebugUndefined.__slots__, StrictUndefined.__slots__
