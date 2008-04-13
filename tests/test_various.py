# -*- coding: utf-8 -*-
"""
    unit test for various things
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.exceptions import TemplateSyntaxError

KEYWORDS = '''\
{{ with }}
{{ as }}
{{ import }}
{{ from }}
{{ class }}
{{ def }}
{{ try }}
{{ except }}
{{ exec }}
{{ global }}
{{ assert }}
{{ break }}
{{ continue }}
{{ lambda }}
{{ return }}
{{ raise }}
{{ yield }}
{{ while }}
{{ pass }}
{{ finally }}'''
UNPACKING = '''{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}'''
RAW = '''{% raw %}{{ FOO }} and {% BAR %}{% endraw %}'''
CONST = '''{{ true }}|{{ false }}|{{ none }}|{{ undefined }}|\
{{ none is defined }}|{{ undefined is defined }}'''
LOCALSET = '''{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1 %}{% endfor %}\
{{ foo }}'''
NONLOCALSET = '''{% set foo = 0 %}\
{% for item in [1, 2] %}{% set foo = 1! %}{% endfor %}\
{{ foo }}'''
CONSTASS1 = '''{% set true = 42 %}'''
CONSTASS2 = '''{% for undefined in seq %}{% endfor %}'''


def test_keywords(env):
    env.from_string(KEYWORDS)


def test_unpacking(env):
    tmpl = env.from_string(UNPACKING)
    assert tmpl.render() == '1|2|3'


def test_raw(env):
    tmpl = env.from_string(RAW)
    assert tmpl.render() == '{{ FOO }} and {% BAR %}'


def test_crazy_raw():
    from jinja2 import Environment
    env = Environment('{', '}', '{', '}')
    tmpl = env.from_string('{raw}{broken foo}{endraw}')
    assert tmpl.render() == '{broken foo}'


def test_cache_dict():
    from jinja2.utils import CacheDict
    d = CacheDict(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["a"]
    d["d"] = 4
    assert len(d) == 3
    assert 'a' in d and 'c' in d and 'd' in d and 'b' not in d


def test_stringfilter(env):
    from jinja2.filters import stringfilter
    f = stringfilter(lambda f, x: f + x)
    assert f('42')(env, None, 23) == '2342'


def test_simplefilter(env):
    from jinja2.filters import simplefilter
    f = simplefilter(lambda f, x: f + x)
    assert f(42)(env, None, 23) == 65


def test_const(env):
    tmpl = env.from_string(CONST)
    assert tmpl.render() == 'True|False|||True|False'


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


def test_nonlocalset(env):
    tmpl = env.from_string(NONLOCALSET)
    assert tmpl.render() == '1'
