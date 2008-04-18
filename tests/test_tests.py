# -*- coding: utf-8 -*-
"""
    unit test for the test functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

DEFINED = '''{{ missing is defined }}|{{ true is defined }}'''
EVEN = '''{{ 1 is even }}|{{ 2 is even }}'''
LOWER = '''{{ "foo" is lower }}|{{ "FOO" is lower }}'''
NUMERIC = '''{{ "43" is numeric }}|{{ "foo" is numeric }}|\
{{ 42 is numeric }}'''
ODD = '''{{ 1 is odd }}|{{ 2 is odd }}'''
SEQUENCE = '''{{ [1, 2, 3] is sequence }}|\
{{ "foo" is sequence }}|\
{{ 42 is sequence }}'''
UPPER = '''{{ "FOO" is upper }}|{{ "foo" is upper }}'''
SAMEAS = '''{{ foo is sameas(false) }}|{{ 0 is sameas(false) }}'''
NOPARENFORARG1 = '''{{ foo is sameas none }}'''


def test_defined(env):
    tmpl = env.from_string(DEFINED)
    assert tmpl.render() == 'False|True'


def test_even(env):
    tmpl = env.from_string(EVEN)
    assert tmpl.render() == 'False|True'


def test_lower(env):
    tmpl = env.from_string(LOWER)
    assert tmpl.render() == 'True|False'


def test_numeric(env):
    tmpl = env.from_string(NUMERIC)
    assert tmpl.render() == 'True|False|True'


def test_odd(env):
    tmpl = env.from_string(ODD)
    assert tmpl.render() == 'True|False'


def test_sequence(env):
    tmpl = env.from_string(SEQUENCE)
    assert tmpl.render() == 'True|True|False'


def test_upper(env):
    tmpl = env.from_string(UPPER)
    assert tmpl.render() == 'True|False'


def test_sameas(env):
    tmpl = env.from_string(SAMEAS)
    assert tmpl.render(foo=False) == 'True|False'


def test_no_paren_for_arg1(env):
    tmpl = env.from_string(NOPARENFORARG1)
    assert tmpl.render(foo=None) == 'True'
