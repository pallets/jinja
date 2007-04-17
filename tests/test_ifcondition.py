# -*- coding: utf-8 -*-
"""
    unit test for if conditions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

SIMPLE = '''{% if true %}...{% endif %}'''
ELIF = '''{% if false %}XXX{% elif true %}...{% else %}XXX{% endif %}'''
ELSE = '''{% if false %}XXX{% else %}...{% endif %}'''
EMPTY = '''[{% if true %}{% else %}{% endif %}]'''


def test_simple(env):
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render() == '...'


def test_elif(env):
    tmpl = env.from_string(ELIF)
    assert tmpl.render() == '...'


def test_else(env):
    tmpl = env.from_string(ELSE)
    assert tmpl.render() == '...'


def test_empty(env):
    tmpl = env.from_string(EMPTY)
    assert tmpl.render() == '[]'
