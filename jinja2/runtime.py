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


__all__ = ['extends', 'subscribe', 'TemplateContext']


def extends(template, namespace):
    """This loads a template (and evaluates it) and replaces the blocks."""


def subscribe(obj, argument, undefined_factory):
    """Get an item or attribute of an object."""
    try:
        return getattr(obj, argument)
    except AttributeError:
        try:
            return obj[argument]
        except LookupError:
            return undefined_factory(attr=argument)


class TemplateContext(dict):

    def __init__(self, globals, undefined_factory, filename):
        dict.__init__(self)
        self.globals = globals
        self.undefined_factory = undefined_factory
        self.filename = filename
        self.filters = {}
        self.tests = {}

    # if there is a default dict, dict has a __missing__ method we can use.
    if defaultdict is None:
        def __getitem__(self, name):
            if name in self:
                return self[name]
            elif name in self.globals:
                return self.globals[name]
            return self.undefined_factory(name)
    else:
        def __missing__(self, key):
            try:
                return self.globals[key]
            except:
                return self.undefined_factory(key)


class Macro(object):

    def __init__(self, func, name, arguments, defaults, catch_all):
        self.func = func
        self.name = name
        self.arguments = arguments
        self.defaults = defaults
        self.catch_all = catch_all

    def __call__(self, *args, **kwargs):
        if len(args) > len(self.arguments):
            raise TypeError('macro %r takes not more than %d argument(s).' %
                            (self.name, len(self.arguments)))
        arguments = {}
        # XXX: assemble arguments
        return u''.join(self.func(*args, **kwargs))
