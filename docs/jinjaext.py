# -*- coding: utf-8 -*-
"""
    Jinja Documentation Extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Support for automatically documenting filters and tests.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import inspect
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.ext.autodoc import prepare_docstring


def format_filter(name, aliases, func):
    try:
        argspec = inspect.getargspec(func)
    except:
        try:
            argspec = inspect.getargspec(func.__init__)
        except:
            try:
                argspec = inspect.getargspec(func.__new__)
            except:
                return []
        del argspec[0][0]
    if getattr(func, 'environmentfilter', False) or \
       getattr(func, 'contextfilter', False):
        del argspec[0][0]
    signature = inspect.formatargspec(*argspec)
    result = ['.. function:: %s%s' % (name, signature), '']
    for line in inspect.getdoc(func).splitlines():
        result.append('    ' + line)
    if aliases:
        result.extend(('', '    :aliases: %s' % ', '.join(
                      '``%s``' % x for x in sorted(aliases))))
    return result


def jinja_filters(dirname, arguments, options, content, lineno,
                  content_offset, block_text, state, state_machine):
    from jinja2.defaults import DEFAULT_FILTERS
    mapping = {}
    for name, func in DEFAULT_FILTERS.iteritems():
        mapping.setdefault(func, []).append(name)
    filters = []
    for func, names in mapping.iteritems():
        aliases = sorted(names, key=lambda x: len(x))
        name = aliases.pop()
        filters.append((name, aliases, func))
    filters.sort()

    result = ViewList()
    for name, aliases, func in filters:
        for item in format_filter(name, aliases, func):
            result.append(item, '<jinjaext>')

    node = nodes.paragraph()
    state.nested_parse(result, content_offset, node)
    return node.children


def setup(app):
    app.add_directive('jinjafilters', jinja_filters, 1, (0, 0, 0))
