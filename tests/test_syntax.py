# -*- coding: utf-8 -*-
"""
    unit test for expression syntax
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

CALL = '''{{ foo('a', c='d', e='f', *['b'], **{'g': 'h'}) }}'''
SLICING = '''{{ [1, 2, 3][:] }}|{{ [1, 2, 3][::-1] }}'''
ATTR = '''{{ foo.bar }}|{{ foo['bar'] }}'''
SUBSCRIPT = '''{{ foo[0] }}|{{ foo[-1] }}'''
KEYATTR = '''{{ {'items': 'foo'}.items }}|{{ {}.items() }}'''
TUPLE = '''{{ () }}'''
MATH = '''{{ (1 + 1 * 2) - 3 / 2 }}|{{ 2**3 }}'''
DIV = '''{{ 3 // 2 }}|{{ 3 / 2 }}|{{ 3 % 2 }}'''
UNARY = '''{{ +3 }}|{{ -3 }}'''
COMPARE = '''{{ 1 > 0 }}|{{ 1 >= 1 }}|{{ 2 < 3 }}|{{ 2 == 2 }}|{{ 1 <= 1 }}'''
LITERALS = '''{{ [] }}|{{ {} }}|{{ '' }}'''
BOOL = '''{{ true and false }}|{{ false or true }}|{{ not false }}'''


def test_call():
    from jinja import Environment
    env = Environment()
    env.globals['foo'] = lambda a, b, c, e, g: a + b + c + e + g
    tmpl = env.from_string(CALL)
    assert tmpl.render() == 'abdfh'


def test_slicing(env):
    tmpl = env.from_string(SLICING)
    assert tmpl.render() == '[1, 2, 3]|[3, 2, 1]'


def test_attr(env):
    tmpl = env.from_string(ATTR)
    assert tmpl.render(foo={'bar': 42}) == '42|42'


def test_subscript(env):
    tmpl = env.from_string(SUBSCRIPT)
    assert tmpl.render(foo=[0, 1, 2]) == '0|2'


def test_keyattr(env):
    tmpl = env.from_string(KEYATTR)
    assert tmpl.render() == 'foo|[]'


def test_tuple(env):
    tmpl = env.from_string(TUPLE)
    assert tmpl.render() == '[]'


def test_math(env):
    tmpl = env.from_string(MATH)
    assert tmpl.render() == '1.5|8'


def test_div(env):
    tmpl = env.from_string(DIV)
    assert tmpl.render() == '1|1.5|1'


def test_unary(env):
    tmpl = env.from_string(UNARY)
    assert tmpl.render() == '3|-3'


def test_compare(env):
    tmpl = env.from_string(COMPARE)
    assert tmpl.render() == 'True|True|True|True|True'


def test_literals(env):
    tmpl = env.from_string(LITERALS)
    assert tmpl.render() == '[]|{}|'


def test_bool(env):
    tmpl = env.from_string(BOOL)
    assert tmpl.render() == 'False|True|True'
