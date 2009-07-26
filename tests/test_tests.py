# -*- coding: utf-8 -*-
"""
    unit test for the test functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, Markup
env = Environment()


DEFINED = '''{{ missing is defined }}|{{ true is defined }}'''
EVEN = '''{{ 1 is even }}|{{ 2 is even }}'''
LOWER = '''{{ "foo" is lower }}|{{ "FOO" is lower }}'''
ODD = '''{{ 1 is odd }}|{{ 2 is odd }}'''
SEQUENCE = '''{{ [1, 2, 3] is sequence }}|\
{{ "foo" is sequence }}|\
{{ 42 is sequence }}'''
UPPER = '''{{ "FOO" is upper }}|{{ "foo" is upper }}'''
SAMEAS = '''{{ foo is sameas false }}|{{ 0 is sameas false }}'''
NOPARENFORARG1 = '''{{ foo is sameas none }}'''
TYPECHECKS = '''\
{{ 42 is undefined }}
{{ 42 is defined }}
{{ 42 is none }}
{{ none is none }}
{{ 42 is number }}
{{ 42 is string }}
{{ "foo" is string }}
{{ "foo" is sequence }}
{{ [1] is sequence }}
{{ range is callable }}
{{ 42 is callable }}
{{ range(5) is iterable }}'''


def test_defined():
    tmpl = env.from_string(DEFINED)
    assert tmpl.render() == 'False|True'


def test_even():
    tmpl = env.from_string(EVEN)
    assert tmpl.render() == 'False|True'


def test_odd():
    tmpl = env.from_string(ODD)
    assert tmpl.render() == 'True|False'


def test_lower():
    tmpl = env.from_string(LOWER)
    assert tmpl.render() == 'True|False'


def test_typechecks():
    tmpl = env.from_string(TYPECHECKS)
    assert tmpl.render() == ''


def test_sequence():
    tmpl = env.from_string(SEQUENCE)
    assert tmpl.render() == 'True|True|False'


def test_upper():
    tmpl = env.from_string(UPPER)
    assert tmpl.render() == 'True|False'


def test_sameas():
    tmpl = env.from_string(SAMEAS)
    assert tmpl.render(foo=False) == 'True|False'


def test_typechecks():
    tmpl = env.from_string(TYPECHECKS)
    assert tmpl.render() == (
        'False\nTrue\nFalse\nTrue\nTrue\nFalse\n'
        'True\nTrue\nTrue\nTrue\nFalse\nTrue'
    )


def test_no_paren_for_arg1():
    tmpl = env.from_string(NOPARENFORARG1)
    assert tmpl.render(foo=None) == 'True'


def test_escaped():
    env = Environment(autoescape=True)
    tmpl = env.from_string('{{ x is escaped }}|{{ y is escaped }}')
    assert tmpl.render(x='foo', y=Markup('foo')) == 'False|True'
