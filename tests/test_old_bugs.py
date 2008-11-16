# -*- coding: utf-8 -*-
"""
    Tests for old bugs
    ~~~~~~~~~~~~~~~~~~

    Unittest that test situations caused by various older bugs.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from jinja2 import Environment, DictLoader


def test_keyword_folding():
    env = Environment()
    env.filters['testing'] = lambda value, some: value + some
    assert env.from_string("{{ 'test'|testing(some='stuff') }}") \
           .render() == 'teststuff'


def test_extends_output_bugs():
    env = Environment(loader=DictLoader({
        'parent.html': '(({% block title %}{% endblock %}))'
    }))

    t = env.from_string('{% if expr %}{% extends "parent.html" %}{% endif %}'
                        '[[{% block title %}title{% endblock %}]]'
                        '{% for item in [1, 2, 3] %}({{ item }}){% endfor %}')
    assert t.render(expr=False) == '[[title]](1)(2)(3)'
    assert t.render(expr=True) == '((title))'


def test_urlize_filter_escaping(env):
    tmpl = env.from_string('{{ "http://www.example.org/<foo"|urlize }}')
    assert tmpl.render() == '<a href="http://www.example.org/&lt;foo">http://www.example.org/&lt;foo</a>'
