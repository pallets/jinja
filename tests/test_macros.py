# -*- coding: utf-8 -*-
"""
    unit test for the macros
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

SIMPLE = '''\
{% macro say_hello name %}Hello {{ name }}!{% endmacro %}
{{ say_hello('Peter') }}\
'''

KWARGSFAILURE = '''\
{% macro foo bar %}...{% endmacro %}
{{ foo(bar='blub') }}\
'''

SCOPING = '''\
{% macro level1 data1 %}
{% macro level2 data2 %}{{ data1 }}|{{ data2 }}{% endmacro %}
{{ level2('bar') }}{% endmacro %}
{{ level1('foo') }}|{{ level2('bar') }}\
'''

ARGUMENTS = '''\
{% macro m a, b, c='c', d='d' %}{{ a }}|{{ b }}|{{ c }}|{{ d }}{% endmacro %}
{{ m() }}|{{ m('a') }}|{{ m('a', 'b') }}|{{ m(1, 2, 3) }}\
'''

PARENTHESES = '''\
{% macro foo(a, b) %}{{ a }}|{{ b }}{% endmacro %}\
{{ foo(1, 2) }}\
'''

VARARGS = '''\
{% macro test %}{{ varargs|join('|') }}{% endmacro %}\
{{ test(1, 2, 3) }}\
'''

SIMPLECALL = '''\
{% macro test %}[[{{ caller() }}]]{% endmacro %}\
{% call test() %}data{% endcall %}\
'''

COMPLEXCALL = '''\
{% macro test %}[[{{ caller(data='data') }}]]{% endmacro %}\
{% call test() %}{{ data }}{% endcall %}\
'''

CALLERUNDEFINED = '''\
{% set caller = 42 %}\
{% macro test() %}{{ caller is not defined }}{% endmacro %}\
{{ test() }}\
'''


def test_simple(env):
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render() == 'Hello Peter!'


def test_kwargs_failure(env):
    from jinja.exceptions import TemplateRuntimeError
    tmpl = env.from_string(KWARGSFAILURE)
    try:
        tmpl.render()
    except TemplateRuntimeError, e:
        pass
    else:
        raise AssertionError('kwargs failure test failed')


def test_scoping(env):
    tmpl = env.from_string(SCOPING)
    assert tmpl.render() == 'foo|bar|'


def test_arguments(env):
    tmpl = env.from_string(ARGUMENTS)
    assert tmpl.render() == '||c|d|a||c|d|a|b|c|d|1|2|3|d'


def test_parentheses(env):
    tmpl = env.from_string(PARENTHESES)
    assert tmpl.render() == '1|2'


def test_varargs(env):
    tmpl = env.from_string(VARARGS)
    assert tmpl.render() == '1|2|3'


def test_simple_call(env):
    tmpl = env.from_string(SIMPLECALL)
    assert tmpl.render() == '[[data]]'


def test_complex_call(env):
    tmpl = env.from_string(COMPLEXCALL)
    assert tmpl.render() == '[[data]]'


def test_caller_undefined(env):
    tmpl = env.from_string(CALLERUNDEFINED)
    assert tmpl.render() == 'True'
