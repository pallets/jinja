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

def test_simple(env):
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render() == 'Hello Peter!'


def test_kwargs_failure(env):
    tmpl = env.from_string(KWARGSFAILURE)
    try:
        tmpl.render()
    except TypeError, e:
        pass
    else:
        raise AssertionError('kwargs failure test failed')


def test_scoping(env):
    tmpl = env.from_string(SCOPING)
    assert tmpl.render() == 'foo|bar|'


def test_arguments(env):
    tmpl = env.from_string(ARGUMENTS)
    assert tmpl.render() == '||c|d|a||c|d|a|b|c|d|1|2|3|d'
