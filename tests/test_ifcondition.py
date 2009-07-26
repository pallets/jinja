# -*- coding: utf-8 -*-
"""
    unit test for if conditions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import Environment
env = Environment()


SIMPLE = '''{% if true %}...{% endif %}'''
ELIF = '''{% if false %}XXX{% elif true %}...{% else %}XXX{% endif %}'''
ELSE = '''{% if false %}XXX{% else %}...{% endif %}'''
EMPTY = '''[{% if true %}{% else %}{% endif %}]'''


def test_simple():
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render() == '...'


def test_elif():
    tmpl = env.from_string(ELIF)
    assert tmpl.render() == '...'


def test_else():
    tmpl = env.from_string(ELSE)
    assert tmpl.render() == '...'


def test_empty():
    tmpl = env.from_string(EMPTY)
    assert tmpl.render() == '[]'


def test_complete():
    tmpl = env.from_string('{% if a %}A{% elif b %}B{% elif c == d %}'
                           'C{% else %}D{% endif %}')
    assert tmpl.render(a=0, b=False, c=42, d=42.0) == 'C'


def test_no_scope():
    tmpl = env.from_string('{% if a %}{% set foo = 1 %}{% endif %}{{ foo }}')
    assert tmpl.render(a=True) == '1'
    tmpl = env.from_string('{% if true %}{% set foo = 1 %}{% endif %}{{ foo }}')
    assert tmpl.render() == '1'
