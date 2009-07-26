# -*- coding: utf-8 -*-
"""
    unit test for the imports and includes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, DictLoader
from jinja2.exceptions import TemplateNotFound

from nose.tools import assert_raises


test_env = Environment(loader=DictLoader(dict(
    module='{% macro test() %}[{{ foo }}|{{ bar }}]{% endmacro %}',
    header='[{{ foo }}|{{ 23 }}]',
    o_printer='({{ o }})'
)))
test_env.globals['bar'] = 23


def test_context_imports():
    t = test_env.from_string('{% import "module" as m %}{{ m.test() }}')
    assert t.render(foo=42) == '[|23]'
    t = test_env.from_string('{% import "module" as m without context %}{{ m.test() }}')
    assert t.render(foo=42) == '[|23]'
    t = test_env.from_string('{% import "module" as m with context %}{{ m.test() }}')
    assert t.render(foo=42) == '[42|23]'
    t = test_env.from_string('{% from "module" import test %}{{ test() }}')
    assert t.render(foo=42) == '[|23]'
    t = test_env.from_string('{% from "module" import test without context %}{{ test() }}')
    assert t.render(foo=42) == '[|23]'
    t = test_env.from_string('{% from "module" import test with context %}{{ test() }}')
    assert t.render(foo=42) == '[42|23]'


def test_context_include():
    t = test_env.from_string('{% include "header" %}')
    assert t.render(foo=42) == '[42|23]'
    t = test_env.from_string('{% include "header" with context %}')
    assert t.render(foo=42) == '[42|23]'
    t = test_env.from_string('{% include "header" without context %}')
    assert t.render(foo=42) == '[|23]'


def test_include_ignoring_missing():
    t = test_env.from_string('{% include "missing" %}')
    assert_raises(TemplateNotFound, t.render)
    for extra in '', 'with context', 'without context':
        t = test_env.from_string('{% include "missing" ignore missing ' +
                                 extra + ' %}')
        assert t.render() == ''


def test_context_include_with_overrides():
    env = Environment(loader=DictLoader(dict(
        main="{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}",
        item="{{ item }}"
    )))
    assert env.get_template("main").render() == "123"


def test_trailing_comma():
    test_env.from_string('{% from "foo" import bar, baz with context %}')
    test_env.from_string('{% from "foo" import bar, baz, with context %}')
    test_env.from_string('{% from "foo" import bar, with context %}')
    test_env.from_string('{% from "foo" import bar, with, context %}')
    test_env.from_string('{% from "foo" import bar, with with context %}')


def test_exports():
    m = test_env.from_string('''
        {% macro toplevel() %}...{% endmacro %}
        {% macro __private() %}...{% endmacro %}
        {% set variable = 42 %}
        {% for item in [1] %}
            {% macro notthere() %}{% endmacro %}
        {% endfor %}
    ''').module
    assert m.toplevel() == '...'
    assert not hasattr(m, '__missing')
    assert m.variable == 42
    assert not hasattr(m, 'notthere')


def test_unoptimized_scopes():
    t = test_env.from_string("""
        {% macro outer(o) %}
        {% macro inner() %}
        {% include "o_printer" %}
        {% endmacro %}
        {{ inner() }}
        {% endmacro %}
        {{ outer("FOO") }}
    """)
    assert t.render().strip() == '(FOO)'
