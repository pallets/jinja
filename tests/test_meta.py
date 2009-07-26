# -*- coding: utf-8 -*-
"""
    unit test for the meta module
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, meta


def test_find_undeclared_variables():
    env = Environment()
    ast = env.parse('{% set foo = 42 %}{{ bar + foo }}')
    x = meta.find_undeclared_variables(ast)
    assert x == set(['bar'])

    ast = env.parse('{% set foo = 42 %}{{ bar + foo }}'
                    '{% macro meh(x) %}{{ x }}{% endmacro %}'
                    '{% for item in seq %}{{ muh(item) + meh(seq) }}{% endfor %}')
    x = meta.find_undeclared_variables(ast)
    assert x == set(['bar', 'seq', 'muh'])


def test_find_refererenced_templates():
    env = Environment()
    ast = env.parse('{% extends "layout.html" %}{% include helper %}')
    i = meta.find_referenced_templates(ast)
    assert i.next() == 'layout.html'
    assert i.next() is None
    assert list(i) == []

    ast = env.parse('{% extends "layout.html" %}'
                    '{% from "test.html" import a, b as c %}'
                    '{% import "meh.html" as meh %}'
                    '{% include "muh.html" %}')
    i = meta.find_referenced_templates(ast)
    assert list(i) == ['layout.html', 'test.html', 'meh.html', 'muh.html']
