# -*- coding: utf-8 -*-
"""
    unit test for the imports and includes
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, DictLoader


test_env = Environment(loader=DictLoader(dict(
    module='{% macro test() %}[{{ foo }}|{{ bar }}]{% endmacro %}',
    header='[{{ foo }}|{{ 23 }}]'
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


def test_trailing_comma():
    test_env.from_string('{% from "foo" import bar, baz with context %}')
    test_env.from_string('{% from "foo" import bar, baz, with context %}')
    test_env.from_string('{% from "foo" import bar, with context %}')
    test_env.from_string('{% from "foo" import bar, with, context %}')
    test_env.from_string('{% from "foo" import bar, with with context %}')
