# -*- coding: utf-8 -*-
"""
    Heavy tests
    ~~~~~~~~~~~

    The tests in this module test complex Jinja2 situations to ensure
    corner cases (unfortunately mostly undocumented scoping behavior)
    does not change between versions.

    :copyright: Copyright 2009 by the Jinja Team.
    :license: BSD.
"""
from jinja2 import Environment
env = Environment()


def test_assigned_scoping():
    t = env.from_string('''
    {%- for item in (1, 2, 3, 4) -%}
        [{{ item }}]
    {%- endfor %}
    {{- item -}}
    ''')
    assert t.render(item=42) == '[1][2][3][4]42'

    t = env.from_string('''
    {%- for item in (1, 2, 3, 4) -%}
        [{{ item }}]
    {%- endfor %}
    {%- set item = 42 %}
    {{- item -}}
    ''')
    assert t.render() == '[1][2][3][4]42'

    t = env.from_string('''
    {%- set item = 42 %}
    {%- for item in (1, 2, 3, 4) -%}
        [{{ item }}]
    {%- endfor %}
    {{- item -}}
    ''')
    assert t.render() == '[1][2][3][4]42'


def test_closure_scoping():
    t = env.from_string('''
    {%- set wrapper = "<FOO>" %}
    {%- for item in (1, 2, 3, 4) %}
        {%- macro wrapper() %}[{{ item }}]{% endmacro %}
        {{- wrapper() }}
    {%- endfor %}
    {{- wrapper -}}
    ''')
    assert t.render() == '[1][2][3][4]<FOO>'

    t = env.from_string('''
    {%- for item in (1, 2, 3, 4) %}
        {%- macro wrapper() %}[{{ item }}]{% endmacro %}
        {{- wrapper() }}
    {%- endfor %}
    {%- set wrapper = "<FOO>" %}
    {{- wrapper -}}
    ''')
    assert t.render() == '[1][2][3][4]<FOO>'

    t = env.from_string('''
    {%- for item in (1, 2, 3, 4) %}
        {%- macro wrapper() %}[{{ item }}]{% endmacro %}
        {{- wrapper() }}
    {%- endfor %}
    {{- wrapper -}}
    ''')
    assert t.render(wrapper=23) == '[1][2][3][4]23'
