# -*- coding: utf-8 -*-
"""
    jinja2.runtime
    ~~~~~~~~~~~~~~

    Runtime helpers.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
try:
    from collections import defaultdict
except ImportError:
    defaultdict = None


# contains only the variables the template will import automatically, not the
# objects injected by the evaluation loop (such as undefined objects)
__all__ = ['extends', 'subscribe', 'LoopContext', 'StaticLoopContext',
           'TemplateContext', 'Macro']


def extends(template, namespace):
    """This loads a template (and evaluates it) and replaces the blocks."""


def subscribe(obj, argument, undefined_factory):
    """Get an item or attribute of an object."""
    try:
        return getattr(obj, str(argument))
    except (AttributeError, UnicodeError):
        try:
            return obj[argument]
        except LookupError:
            return undefined_factory(attr=argument)


class TemplateContext(dict):
    """
    Holds the variables of the local template or of the global one.  It's
    not save to use this class outside of the compiled code.  For example
    update and other methods will not work as they seem (they don't update
    the exported variables for example).
    """

    def __init__(self, globals, undefined_factory, filename):
        dict.__init__(self, globals)
        self.exported = set()
        self.undefined_factory = undefined_factory
        self.filename = filename
        self.filters = {}
        self.tests = {}

    def __setitem__(self, key, value):
        """If we set items to the dict we track the variables set so
        that includes can access the exported variables."""
        dict.__setitem__(self, key, value)
        self.exported.add(key)

    def __delitem__(self, key):
        """On delete we no longer export it."""
        dict.__delitem__(self, key)
        self.exported.dicard(key)

    def get_exported(self):
        """Get a dict of all exported variables."""
        return dict((k, self[k]) for k in self.exported)

    # if there is a default dict, dict has a __missing__ method we can use.
    if defaultdict is None:
        def __getitem__(self, name):
            if name in self:
                return self[name]
            return self.undefined_factory(name)
    else:
        def __missing__(self, key):
            return self.undefined_factory(key)


class LoopContextBase(object):
    """Helper for extended iteration."""

    def __init__(self, iterable, parent=None):
        self._iterable = iterable
        self._length = None
        self.index0 = 0
        self.parent = parent

    first = property(lambda x: x.index0 == 0)
    last = property(lambda x: x.revindex0 == 0)
    index = property(lambda x: x.index0 + 1)
    revindex = property(lambda x: x.length)
    revindex0 = property(lambda x: x.length - 1)
    length = property(lambda x: len(x))


class LoopContext(LoopContextBase):

    def __init__(self, iterable, parent=None, enforce_length=False):
        self._iterable = iterable
        self._length = None
        self.index0 = 0
        self.parent = parent
        if enforce_length:
            len(self)

    def make_static(self):
        """Return a static loop context for the optimizer."""
        parent = None
        if self.parent is not None:
            parent = self.parent.make_static()
        return StaticLoopContext(self.index0, self.length, parent)

    def __iter__(self):
        for item in self._iterable:
            yield self, item
            self.index0 += 1

    def __len__(self):
        if self._length is None:
            try:
                length = len(self._iterable)
            except TypeError:
                self._iterable = tuple(self._iterable)
                length = self.index0 + len(tuple(self._iterable))
            self._length = length
        return self._length


class StaticLoopContext(LoopContextBase):

    def __init__(self, index0, length, parent):
        self.index0 = index0
        self.parent = parent
        self._length = length

    def __repr__(self):
        return 'StaticLoopContext(%r, %r, %r)' % (
            self.index0,
            self._length,
            self.parent
        )

    def make_static(self):
        return self


class Macro(object):
    """
    Wraps a macor
    """

    def __init__(self, func, name, arguments, defaults, catch_all, \
                 undefined_factory):
        self.func = func
        self.name = name
        self.arguments = arguments
        self.defaults = defaults
        self.catch_all = catch_all
        self.undefined_factory = undefined_factory

    def __call__(self, *args, **kwargs):
        arg_count = len(self.arguments)
        if len(args) > arg_count:
            raise TypeError('macro %r takes not more than %d argument(s).' %
                            (self.name, len(self.arguments)))
        arguments = {}
        for idx, name in enumerate(self.arguments):
            try:
                value = args[idx]
            except IndexError:
                try:
                    value = kwargs.pop(name)
                except KeyError:
                    try:
                        value = self.defaults[idx - arg_count]
                    except IndexError:
                        value = self.undefined_factory(name)
            arguments['l_' + name] = arg
        if self.catch_all:
            arguments['l_arguments'] = kwargs
        return u''.join(self.func(**arguments))


class Undefined(object):
    """The default undefined behavior."""

    def __init__(self, name=None, attr=None):
        if attr is None:
            self._undefined_hint = '%r is undefined' % attr
        elif name is None:
            self._undefined_hint = 'attribute %r is undefined' % name
        else:
            self._undefined_hint = 'attribute %r of %r is undefined' \
                                   % (attr, name)

    def fail(self, *args, **kwargs):
        raise TypeError(self._undefined_hint)
    __getattr__ = __getitem__ = __add__ = __mul__ = __div__ = \
    __realdiv__ = __floordiv__ = __mod__ = __pos__ = __neg__ = fail
    del fail

    def __unicode__(self):
        return ''

    def __repr__(self):
        return 'Undefined'

    def __len__(self):
        return 0

    def __iter__(self):
        if 0:
            yield None
