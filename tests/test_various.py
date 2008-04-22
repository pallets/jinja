# -*- coding: utf-8 -*-
"""
    unit test for various things
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.exceptions import TemplateSyntaxError


UNPACKING = '''{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}'''
RAW = '''{% raw %}{{ FOO }} and {% BAR %}{% endraw %}'''
CONST = '''{{ true }}|{{ false }}|{{ none }}|\
{{ none is defined }}|{{ missing is defined }}'''
LOCALSET = '''{% foo = 0 %}\
{% for item in [1, 2] %}{% foo = 1 %}{% endfor %}\
{{ foo }}'''
CONSTASS1 = '''{% true = 42 %}'''
CONSTASS2 = '''{% for none in seq %}{% endfor %}'''


def test_unpacking(env):
    tmpl = env.from_string(UNPACKING)
    assert tmpl.render() == '1|2|3'


def test_raw(env):
    tmpl = env.from_string(RAW)
    assert tmpl.render() == '{{ FOO }} and {% BAR %}'


def test_lru_cache():
    from jinja2.utils import LRUCache
    d = LRUCache(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["a"]
    d["d"] = 4
    assert len(d) == 3
    assert 'a' in d and 'c' in d and 'd' in d and 'b' not in d


def test_const(env):
    tmpl = env.from_string(CONST)
    assert tmpl.render() == 'True|False|None|True|False'


def test_const_assign(env):
    for tmpl in CONSTASS1, CONSTASS2:
        try:
            env.from_string(tmpl)
        except TemplateSyntaxError:
            pass
        else:
            raise AssertionError('expected syntax error')


def test_localset(env):
    tmpl = env.from_string(LOCALSET)
    assert tmpl.render() == '0'
