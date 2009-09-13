# -*- coding: utf-8 -*-
"""
    Tests for old bugs
    ~~~~~~~~~~~~~~~~~~

    Unittest that test situations caused by various older bugs.

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD.
"""
from jinja2 import Environment, DictLoader, TemplateSyntaxError

env = Environment()

from nose.tools import assert_raises


def test_keyword_folding():
    env = Environment()
    env.filters['testing'] = lambda value, some: value + some
    assert env.from_string("{{ 'test'|testing(some='stuff') }}") \
           .render() == 'teststuff'


def test_extends_output_bugs():
    env = Environment(loader=DictLoader({
        'parent.html': '(({% block title %}{% endblock %}))'
    }))

    t = env.from_string('{% if expr %}{% extends "parent.html" %}{% endif %}'
                        '[[{% block title %}title{% endblock %}]]'
                        '{% for item in [1, 2, 3] %}({{ item }}){% endfor %}')
    assert t.render(expr=False) == '[[title]](1)(2)(3)'
    assert t.render(expr=True) == '((title))'


def test_urlize_filter_escaping():
    tmpl = env.from_string('{{ "http://www.example.org/<foo"|urlize }}')
    assert tmpl.render() == '<a href="http://www.example.org/&lt;foo">http://www.example.org/&lt;foo</a>'


def test_loop_call_loop():
    tmpl = env.from_string('''

    {% macro test() %}
        {{ caller() }}
    {% endmacro %}

    {% for num1 in range(5) %}
        {% call test() %}
            {% for num2 in range(10) %}
                {{ loop.index }}
            {% endfor %}
        {% endcall %}
    {% endfor %}

    ''')

    assert tmpl.render().split() == map(unicode, range(1, 11)) * 5


def test_weird_inline_comment():
    env = Environment(line_statement_prefix='%')
    assert_raises(TemplateSyntaxError, env.from_string,
                  '% for item in seq {# missing #}\n...% endfor')


def test_old_macro_loop_scoping_bug():
    tmpl = env.from_string('{% for i in (1, 2) %}{{ i }}{% endfor %}'
                           '{% macro i() %}3{% endmacro %}{{ i() }}')
    assert tmpl.render() == '123'
