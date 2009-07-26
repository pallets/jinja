# -*- coding: utf-8 -*-
"""
    unit test for expression syntax
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

from nose.tools import assert_raises

env = Environment()


CALL = '''{{ foo('a', c='d', e='f', *['b'], **{'g': 'h'}) }}'''
SLICING = '''{{ [1, 2, 3][:] }}|{{ [1, 2, 3][::-1] }}'''
ATTR = '''{{ foo.bar }}|{{ foo['bar'] }}'''
SUBSCRIPT = '''{{ foo[0] }}|{{ foo[-1] }}'''
TUPLE = '''{{ () }}|{{ (1,) }}|{{ (1, 2) }}'''
MATH = '''{{ (1 + 1 * 2) - 3 / 2 }}|{{ 2**3 }}'''
DIV = '''{{ 3 // 2 }}|{{ 3 / 2 }}|{{ 3 % 2 }}'''
UNARY = '''{{ +3 }}|{{ -3 }}'''
CONCAT = '''{{ [1, 2] ~ 'foo' }}'''
COMPARE = '''{{ 1 > 0 }}|{{ 1 >= 1 }}|{{ 2 < 3 }}|{{ 2 == 2 }}|{{ 1 <= 1 }}'''
INOP = '''{{ 1 in [1, 2, 3] }}|{{ 1 not in [1, 2, 3] }}'''
LITERALS = '''{{ [] }}|{{ {} }}|{{ () }}'''
BOOL = '''{{ true and false }}|{{ false or true }}|{{ not false }}'''
GROUPING = '''{{ (true and false) or (false and true) and not false }}'''
CONDEXPR = '''{{ 0 if true else 1 }}'''
DJANGOATTR = '''{{ [1, 2, 3].0 }}|{{ [[1]].0.0 }}'''
FILTERPRIORITY = '''{{ "foo"|upper + "bar"|upper }}'''
TUPLETEMPLATES = [
    '{{ () }}',
    '{{ (1, 2) }}',
    '{{ (1, 2,) }}',
    '{{ 1, }}',
    '{{ 1, 2 }}',
    '{% for foo, bar in seq %}...{% endfor %}',
    '{% for x in foo, bar %}...{% endfor %}',
    '{% for x in foo, %}...{% endfor %}'
]
TRAILINGCOMMA = '''{{ (1, 2,) }}|{{ [1, 2,] }}|{{ {1: 2,} }}'''


def test_call():
    env = Environment()
    env.globals['foo'] = lambda a, b, c, e, g: a + b + c + e + g
    tmpl = env.from_string(CALL)
    assert tmpl.render() == 'abdfh'


def test_slicing():
    tmpl = env.from_string(SLICING)
    assert tmpl.render() == '[1, 2, 3]|[3, 2, 1]'


def test_attr():
    tmpl = env.from_string(ATTR)
    assert tmpl.render(foo={'bar': 42}) == '42|42'


def test_subscript():
    tmpl = env.from_string(SUBSCRIPT)
    assert tmpl.render(foo=[0, 1, 2]) == '0|2'


def test_tuple():
    tmpl = env.from_string(TUPLE)
    assert tmpl.render() == '()|(1,)|(1, 2)'


def test_math():
    tmpl = env.from_string(MATH)
    assert tmpl.render() == '1.5|8'


def test_div():
    tmpl = env.from_string(DIV)
    assert tmpl.render() == '1|1.5|1'


def test_unary():
    tmpl = env.from_string(UNARY)
    assert tmpl.render() == '3|-3'


def test_concat():
    tmpl = env.from_string(CONCAT)
    assert tmpl.render() == '[1, 2]foo'


def test_compare():
    tmpl = env.from_string(COMPARE)
    assert tmpl.render() == 'True|True|True|True|True'


def test_inop():
    tmpl = env.from_string(INOP)
    assert tmpl.render() == 'True|False'


def test_literals():
    tmpl = env.from_string(LITERALS)
    assert tmpl.render().lower() == '[]|{}|()'


def test_bool():
    tmpl = env.from_string(BOOL)
    assert tmpl.render() == 'False|True|True'


def test_grouping():
    tmpl = env.from_string(GROUPING)
    assert tmpl.render() == 'False'


def test_django_attr():
    tmpl = env.from_string(DJANGOATTR)
    assert tmpl.render() == '1|1'


def test_conditional_expression():
    tmpl = env.from_string(CONDEXPR)
    assert tmpl.render() == '0'


def test_short_conditional_expression():
    tmpl = env.from_string('<{{ 1 if false }}>')
    assert tmpl.render() == '<>'

    tmpl = env.from_string('<{{ (1 if false).bar }}>')
    assert_raises(UndefinedError, tmpl.render)


def test_filter_priority():
    tmpl = env.from_string(FILTERPRIORITY)
    assert tmpl.render() == 'FOOBAR'


def test_function_calls():
    tests = [
        (True, '*foo, bar'),
        (True, '*foo, *bar'),
        (True, '*foo, bar=42'),
        (True, '**foo, *bar'),
        (True, '**foo, bar'),
        (False, 'foo, bar'),
        (False, 'foo, bar=42'),
        (False, 'foo, bar=23, *args'),
        (False, 'a, b=c, *d, **e'),
        (False, '*foo, **bar')
    ]
    for should_fail, sig in tests:
        if should_fail:
            assert_raises(TemplateSyntaxError, env.from_string, '{{ foo(%s) }}' % sig)
        else:
            env.from_string('foo(%s)' % sig)


def test_tuple_expr():
    for tmpl in TUPLETEMPLATES:
        print tmpl
        assert env.from_string(tmpl)


def test_trailing_comma():
    tmpl = env.from_string(TRAILINGCOMMA)
    assert tmpl.render().lower() == '(1, 2)|[1, 2]|{1: 2}'


def test_block_end_name():
    env.from_string('{% block foo %}...{% endblock foo %}')
    assert_raises(TemplateSyntaxError, env.from_string, '{% block x %}{% endblock y %}')


def test_contant_casing():
    for const in True, False, None:
        tmpl = env.from_string('{{ %s }}|{{ %s }}|{{ %s }}' % (
            str(const), str(const).lower(), str(const).upper()
        ))
        assert tmpl.render() == '%s|%s|' % (const, const)


def test_test_chaining():
    assert_raises(TemplateSyntaxError, env.from_string, '{{ foo is string is sequence }}')
    env.from_string('{{ 42 is string or 42 is number }}').render() == 'True'


def test_string_concatenation():
    tmpl = env.from_string('{{ "foo" "bar" "baz" }}')
    assert tmpl.render() == 'foobarbaz'


def test_notin():
    bar = xrange(100)
    tmpl = env.from_string('''{{ not 42 in bar }}''')
    assert tmpl.render(bar=bar) == unicode(not 42 in bar)


def test_implicit_subscribed_tuple():
    class Foo(object):
        def __getitem__(self, x):
            return x
    t = env.from_string('{{ foo[1, 2] }}')
    assert t.render(foo=Foo()) == u'(1, 2)'
