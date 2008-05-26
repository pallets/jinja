# -*- coding: utf-8 -*-
"""
    unit test for various things
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import gc
from py.test import raises
from jinja2 import escape
from jinja2.exceptions import TemplateSyntaxError


UNPACKING = '''{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}'''
RAW = '''{% raw %}{{ FOO }} and {% BAR %}{% endraw %}'''
CONST = '''{{ true }}|{{ false }}|{{ none }}|\
{{ none is defined }}|{{ missing is defined }}'''
LOCALSET = '''{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1 %}{% endfor %}\
{{ foo }}'''
CONSTASS1 = '''{% set true = 42 %}'''
CONSTASS2 = '''{% for none in seq %}{% endfor %}'''


def test_unpacking(env):
    tmpl = env.from_string(UNPACKING)
    assert tmpl.render() == '1|2|3'


def test_raw(env):
    tmpl = env.from_string(RAW)
    assert tmpl.render() == '{{ FOO }} and {% BAR %}'


def test_const(env):
    tmpl = env.from_string(CONST)
    assert tmpl.render() == 'True|False|None|True|False'


def test_const_assign(env):
    for tmpl in CONSTASS1, CONSTASS2:
        raises(TemplateSyntaxError, env.from_string, tmpl)


def test_localset(env):
    tmpl = env.from_string(LOCALSET)
    assert tmpl.render() == '0'


def test_markup_leaks():
    counts = set()
    for count in xrange(20):
        for item in xrange(1000):
            escape("foo")
            escape("<foo>")
            escape(u"foo")
            escape(u"<foo>")
        counts.add(len(gc.get_objects()))
    assert len(counts) == 1, 'ouch, c extension seems to leak objects'


def test_item_before_attribute():
    from jinja2 import Environment
    from jinja2.sandbox import SandboxedEnvironment

    for env in Environment(), SandboxedEnvironment():
        tmpl = env.from_string('{{ foo.items() }}')
        assert tmpl.render(foo={'items': lambda: 42}) == '42'
        assert tmpl.render(foo={}) == '[]'
