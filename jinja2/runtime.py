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


__all__ = ['extends', 'subscribe', 'LoopContext', 'TemplateContext', 'Macro']


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


class LoopContext(object):
    """Helper for extended iteration."""

    def __init__(self, iterable, parent=None):
        self._iterable = iterable
        self.index0 = 0
        self.parent = parent

    def __iter__(self):
        for item in self._iterable:
            yield self, item
            self.index0 += 1

    first = property(lambda x: x.index0 == 0)
    last = property(lambda x: x.revindex0 == 0)
    index = property(lambda x: x.index0 + 1)
    revindex = property(lambda x: x.length)
    revindex0 = property(lambda x: x.length - 1)

    @property
    def length(self):
        if not hasattr(self, '_length'):
            try:
                length = len(self._iterable)
            except TypeError:
                length = len(tuple(self._iterable))
            self._length = length
        return self._length


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
