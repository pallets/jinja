# -*- coding: utf-8 -*-
"""
    unit test for the macros
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import Environment, DictLoader

env = Environment(trim_blocks=True)


SIMPLE = '''\
{% macro say_hello(name) %}Hello {{ name }}!{% endmacro %}
{{ say_hello('Peter') }}\
'''

SCOPING = '''\
{% macro level1(data1) %}
{% macro level2(data2) %}{{ data1 }}|{{ data2 }}{% endmacro %}
{{ level2('bar') }}{% endmacro %}
{{ level1('foo') }}\
'''

ARGUMENTS = '''\
{% macro m(a, b, c='c', d='d') %}{{ a }}|{{ b }}|{{ c }}|{{ d }}{% endmacro %}
{{ m() }}|{{ m('a') }}|{{ m('a', 'b') }}|{{ m(1, 2, 3) }}\
'''

VARARGS = '''\
{% macro test() %}{{ varargs|join('|') }}{% endmacro %}\
{{ test(1, 2, 3) }}\
'''

SIMPLECALL = '''\
{% macro test() %}[[{{ caller() }}]]{% endmacro %}\
{% call test() %}data{% endcall %}\
'''

COMPLEXCALL = '''\
{% macro test() %}[[{{ caller('data') }}]]{% endmacro %}\
{% call(data) test() %}{{ data }}{% endcall %}\
'''

CALLERUNDEFINED = '''\
{% set caller = 42 %}\
{% macro test() %}{{ caller is not defined }}{% endmacro %}\
{{ test() }}\
'''

INCLUDETEMPLATE = '''{% macro test(foo) %}[{{ foo }}]{% endmacro %}'''


def test_simple():
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render() == 'Hello Peter!'


def test_scoping():
    tmpl = env.from_string(SCOPING)
    assert tmpl.render() == 'foo|bar'


def test_arguments():
    tmpl = env.from_string(ARGUMENTS)
    assert tmpl.render() == '||c|d|a||c|d|a|b|c|d|1|2|3|d'


def test_varargs():
    tmpl = env.from_string(VARARGS)
    assert tmpl.render() == '1|2|3'


def test_simple_call():
    tmpl = env.from_string(SIMPLECALL)
    assert tmpl.render() == '[[data]]'


def test_complex_call():
    tmpl = env.from_string(COMPLEXCALL)
    assert tmpl.render() == '[[data]]'


def test_caller_undefined():
    tmpl = env.from_string(CALLERUNDEFINED)
    assert tmpl.render() == 'True'


def test_include():
    env = Environment(loader=DictLoader({'include': INCLUDETEMPLATE}))
    tmpl = env.from_string('{% from "include" import test %}{{ test("foo") }}')
    assert tmpl.render() == '[foo]'


def test_macro_api():
    tmpl = env.from_string('{% macro foo(a, b) %}{% endmacro %}'
                           '{% macro bar() %}{{ varargs }}{{ kwargs }}{% endmacro %}'
                           '{% macro baz() %}{{ caller() }}{% endmacro %}')
    assert tmpl.module.foo.arguments == ('a', 'b')
    assert tmpl.module.foo.defaults == ()
    assert tmpl.module.foo.name == 'foo'
    assert not tmpl.module.foo.caller
    assert not tmpl.module.foo.catch_kwargs
    assert not tmpl.module.foo.catch_varargs
    assert tmpl.module.bar.arguments == ()
    assert tmpl.module.bar.defaults == ()
    assert not tmpl.module.bar.caller
    assert tmpl.module.bar.catch_kwargs
    assert tmpl.module.bar.catch_varargs
    assert tmpl.module.baz.caller
