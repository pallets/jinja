# -*- coding: utf-8 -*-
"""
    Jinja Documentation Extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Support for automatically documenting filters and tests.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import os
import re
import inspect
import jinja2
from itertools import islice
from types import BuiltinFunctionType
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.ext.autodoc import prepare_docstring
from sphinx.application import TemplateBridge
from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, \
     Number, Operator, Generic
from jinja2 import Environment, FileSystemLoader


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

        String:                     '#AA891C',
        Number:                     '#444444',

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


class Jinja2Bridge(TemplateBridge):

    def init(self, builder):
        path = builder.config.templates_path
        self.env = Environment(loader=FileSystemLoader(path))

    def render(self, template, context):
        return self.env.get_template(template).render(context)


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


def jinja_changelog(dirname, arguments, options, content, lineno,
                    content_offset, block_text, state, state_machine):
    doc = ViewList()
    changelog = file(os.path.join(os.path.dirname(jinja2.__file__), '..',
                                  'CHANGES'))
    try:
        for line in islice(changelog, 3, None):
            doc.append(line.rstrip(), '<jinjaext>')
    finally:
        changelog.close()
    node = nodes.section()
    # hack around title style bookkeeping
    surrounding_title_styles = state.memo.title_styles
    surrounding_section_level = state.memo.section_level
    state.memo.title_styles = []
    state.memo.section_level = 0
    state.nested_parse(doc, content_offset, node, match_titles=1)
    state.memo.title_styles = surrounding_title_styles
    state.memo.section_level = surrounding_section_level
    return node.children


from jinja2.defaults import DEFAULT_FILTERS, DEFAULT_TESTS
jinja_filters = dump_functions(DEFAULT_FILTERS)
jinja_tests = dump_functions(DEFAULT_TESTS)


def setup(app):
    app.add_directive('jinjafilters', jinja_filters, 0, (0, 0, 0))
    app.add_directive('jinjatests', jinja_tests, 0, (0, 0, 0))
    app.add_directive('jinjachangelog', jinja_changelog, 0, (0, 0, 0))
