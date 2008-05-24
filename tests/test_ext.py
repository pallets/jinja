# -*- coding: utf-8 -*-
"""
    unit test for some extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, nodes
from jinja2.ext import Extension


importable_object = 23


class TestExtension(Extension):
    tags = set(['test'])
    ext_attr = 42

    def parse(self, parser):
        return nodes.Output([self.call_method('_dump', [
            nodes.EnvironmentAttribute('sandboxed'),
            self.attr('ext_attr'),
            nodes.ImportedName(__name__ + '.importable_object'),
            nodes.ContextReference()
        ])]).set_lineno(parser.stream.next().lineno)

    def _dump(self, sandboxed, ext_attr, imported_object, context):
        return '%s|%s|%s|%s' % (
            sandboxed,
            ext_attr,
            imported_object,
            context.blocks
        )


def test_loop_controls():
    env = Environment(extensions=['jinja2.ext.loopcontrols'])

    tmpl = env.from_string('''
        {%- for item in [1, 2, 3, 4] %}
            {%- if item % 2 == 0 %}{% continue %}{% endif -%}
            {{ item }}
        {%- endfor %}''')
    assert tmpl.render() == '13'

    tmpl = env.from_string('''
        {%- for item in [1, 2, 3, 4] %}
            {%- if item > 2 %}{% break %}{% endif -%}
            {{ item }}
        {%- endfor %}''')
    assert tmpl.render() == '12'


def test_do():
    env = Environment(extensions=['jinja2.ext.do'])
    tmpl = env.from_string('''
        {%- set items = [] %}
        {%- for char in "foo" %}
            {%- do items.append(loop.index0 ~ char) %}
        {%- endfor %}{{ items|join(', ') }}''')
    assert tmpl.render() == '0f, 1o, 2o'


def test_extension_nodes():
    env = Environment(extensions=[TestExtension])
    tmpl = env.from_string('{% test %}')
    assert tmpl.render() == 'False|42|23|{}'


def test_identifier():
    assert TestExtension.identifier == __name__ + '.TestExtension'


def test_rebinding():
    original = Environment(extensions=[TestExtension])
    overlay = original.overlay()
    for env in original, overlay:
        for ext in env.extensions.itervalues():
            assert ext.environment is env
