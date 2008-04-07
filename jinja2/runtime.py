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


__all__ = ['extends', 'TemplateContext']


def extends(template, namespace):
    """
    This loads a template (and evaluates it) and replaces the blocks.
    """


class TemplateContext(dict):

    def __init__(self, globals, undefined_factory, filename):
        dict.__init__(self, globals)
        self.undefined_factory = undefined_factory
        self.filename = filename

    # if there is a default dict, dict has a __missing__ method we can use.
    if defaultdict is None:
        def __getitem__(self, name):
            if name in self:
                return self[name]
            return self.undefined_factory(name)
    else:
        def __missing__(self, key):
            return self.undefined_factory(key)

    def from_locals(self, mapping):
        """Update the template context from locals."""
        for key, value in mapping.iteritems():
            if key[:2] == 'l_':
                self[key[:-2]] = value
