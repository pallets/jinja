# -*- coding: utf-8 -*-
"""
    unit test for various things
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import gc
from jinja2 import escape, is_undefined, Environment
from jinja2.utils import Cycler
from jinja2.exceptions import TemplateSyntaxError

from nose import SkipTest
from nose.tools import assert_raises

env = Environment()


UNPACKING = '''{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}'''
RAW = '''{% raw %}{{ FOO }} and {% BAR %}{% endraw %}'''
CONST = '''{{ true }}|{{ false }}|{{ none }}|\
{{ none is defined }}|{{ missing is defined }}'''
LOCALSET = '''{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1 %}{% endfor %}\
{{ foo }}'''
CONSTASS1 = '''{% set true = 42 %}'''
CONSTASS2 = '''{% for none in seq %}{% endfor %}'''


def test_unpacking():
    tmpl = env.from_string(UNPACKING)
    assert tmpl.render() == '1|2|3'


def test_raw():
    tmpl = env.from_string(RAW)
    assert tmpl.render() == '{{ FOO }} and {% BAR %}'


def test_const():
    tmpl = env.from_string(CONST)
    assert tmpl.render() == 'True|False|None|True|False'


def test_const_assign():
    for tmpl in CONSTASS1, CONSTASS2:
        assert_raises(TemplateSyntaxError, env.from_string, tmpl)


def test_localset():
    tmpl = env.from_string(LOCALSET)
    assert tmpl.render() == '0'


def test_markup_leaks():
    # this test only tests the c extension
    if hasattr(escape, 'func_code'):
        raise SkipTest()
    counts = set()
    for count in xrange(20):
        for item in xrange(1000):
            escape("foo")
            escape("<foo>")
            escape(u"foo")
            escape(u"<foo>")
        counts.add(len(gc.get_objects()))
    assert len(counts) == 1, 'ouch, c extension seems to leak objects'


def test_item_and_attribute():
    from jinja2.sandbox import SandboxedEnvironment

    for env in Environment(), SandboxedEnvironment():
        tmpl = env.from_string('{{ foo.items() }}')
        assert tmpl.render(foo={'items': 42}) == "[('items', 42)]"
        tmpl = env.from_string('{{ foo|attr("items")() }}')
        assert tmpl.render(foo={'items': 42}) == "[('items', 42)]"
        tmpl = env.from_string('{{ foo["items"] }}')
        assert tmpl.render(foo={'items': 42}) == '42'


def test_finalizer():
    def finalize_none_empty(value):
        if value is None:
            value = u''
        return value
    env = Environment(finalize=finalize_none_empty)
    tmpl = env.from_string('{% for item in seq %}|{{ item }}{% endfor %}')
    assert tmpl.render(seq=(None, 1, "foo")) == '||1|foo'
    tmpl = env.from_string('<{{ none }}>')
    assert tmpl.render() == '<>'


def test_cycler():
    items = 1, 2, 3
    c = Cycler(*items)
    for item in items + items:
        assert c.current == item
        assert c.next() == item
    c.next()
    assert c.current == 2
    c.reset()
    assert c.current == 1


def test_expressions():
    expr = env.compile_expression("foo")
    assert expr() is None
    assert expr(foo=42) == 42
    expr2 = env.compile_expression("foo", undefined_to_none=False)
    assert is_undefined(expr2())

    expr = env.compile_expression("42 + foo")
    assert expr(foo=42) == 84
