# -*- coding: utf-8 -*-
"""
    Jinja Documentation Extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Support for automatically documenting filters and tests.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import re
import inspect
from types import BuiltinFunctionType
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.ext.autodoc import prepare_docstring


from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, \
     Number, Operator, Generic


class JinjaStyle(Style):
    title = 'Jinja Style'
    default_style = ""
    styles = {
        Comment:                    'italic #aaaaaa',
        Comment.Preproc:            'noitalic #B11414',
        Comment.Special:            'italic #505050',

        Keyword:                    'bold #B80000',
        Keyword.Type:               '#808080',

        Operator.Word:              '#333333',

        Name.Builtin:               '#333333',
        Name.Function:              '#333333',
        Name.Class:                 'bold #333333',
        Name.Namespace:             'bold #333333',
        Name.Entity:                'bold #363636',
        Name.Attribute:             '#686868',
        Name.Tag:                   'bold #686868',
        Name.Decorator:             '#686868',

        String:                     '#BE9B5D',
        Number:                     '#FF0000',

        Generic.Heading:            'bold #000080',
        Generic.Subheading:         'bold #800080',
        Generic.Deleted:            '#aa0000',
        Generic.Inserted:           '#00aa00',
        Generic.Error:              '#aa0000',
        Generic.Emph:               'italic',
        Generic.Strong:             'bold',
        Generic.Prompt:             '#555555',
        Generic.Output:             '#888888',
        Generic.Traceback:          '#aa0000',

        Error:                      '#F00 bg:#FAA'
    }

_sig_re = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\(.*?\))')


def format_function(name, aliases, func):
    lines = inspect.getdoc(func).splitlines()
    signature = '()'
    if isinstance(func, BuiltinFunctionType):
        match = _sig_re.match(lines[0])
        if match is not None:
            del lines[:1 + bool(lines and not lines[0])]
            signature = match.group(1)
    else:
        try:
            argspec = inspect.getargspec(func)
            if getattr(func, 'environmentfilter', False) or \
               getattr(func, 'contextfilter', False):
                del argspec[0][0]
            signature = inspect.formatargspec(*argspec)
        except:
            pass
    result = ['.. function:: %s%s' % (name, signature), '']
    result.extend('    ' + line for line in lines)
    if aliases:
        result.extend(('', '    :aliases: %s' % ', '.join(
                      '``%s``' % x for x in sorted(aliases))))
    return result


def dump_functions(mapping):
    def directive(dirname, arguments, options, content, lineno,
                      content_offset, block_text, state, state_machine):
        reverse_mapping = {}
        for name, func in mapping.iteritems():
            reverse_mapping.setdefault(func, []).append(name)
        filters = []
        for func, names in reverse_mapping.iteritems():
            aliases = sorted(names, key=lambda x: len(x))
            name = aliases.pop()
            filters.append((name, aliases, func))
        filters.sort()

        result = ViewList()
        for name, aliases, func in filters:
            for item in format_function(name, aliases, func):
                result.append(item, '<jinjaext>')

        node = nodes.paragraph()
        state.nested_parse(result, content_offset, node)
        return node.children
    return directive


from jinja2.defaults import DEFAULT_FILTERS, DEFAULT_TESTS
jinja_filters = dump_functions(DEFAULT_FILTERS)
jinja_tests = dump_functions(DEFAULT_TESTS)


def setup(app):
    app.add_directive('jinjafilters', jinja_filters, 0, (0, 0, 0))
    app.add_directive('jinjatests', jinja_tests, 0, (0, 0, 0))
