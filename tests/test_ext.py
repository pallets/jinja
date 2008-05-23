# -*- coding: utf-8 -*-
"""
    unit test for some extensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment


def test_loop_controls():
    env = Environment(extensions=['jinja2.ext.loopcontrols'])

    tmpl = env.from_string('''
        {%- for item in [1, 2, 3, 4] %}
            {%- if item % 2 == 0 %}{% continue %}{% endif -%}
            {{ item }}
        {%- endfor %}''')
    assert tmpl.render() == '13'

    tmpl = env.from_string('''
        {%- for item in [1, 2, 3, 4] %}
            {%- if item > 2 %}{% break %}{% endif -%}
            {{ item }}
        {%- endfor %}''')
    assert tmpl.render() == '12'


def test_do():
    env = Environment(extensions=['jinja2.ext.do'])
    tmpl = env.from_string('''
        {%- set items = [] %}
        {%- for char in "foo" %}
            {%- do items.append(loop.index0 ~ char) %}
        {%- endfor %}{{ items|join(', ') }}''')
    assert tmpl.render() == '0f, 1o, 2o'
