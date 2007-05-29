# -*- coding: utf-8 -*-
"""
    unit test for various things
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

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
CALL = '''{{ foo('a', c='d', e='f', *['b'], **{'g': 'h'}) }}'''


def test_keywords(env):
    env.from_string(KEYWORDS)


def test_unpacking(env):
    tmpl = env.from_string(UNPACKING)
    assert tmpl.render() == '1|2|3'


def test_raw(env):
    tmpl = env.from_string(RAW)
    assert tmpl.render() == '{{ FOO }} and {% BAR %}'


def test_crazy_raw():
    from jinja import Environment
    env = Environment('{', '}', '{', '}')
    tmpl = env.from_string('{raw}{broken foo}{endraw}')
    assert tmpl.render() == '{broken foo}'


def test_cache_dict():
    from jinja.utils import CacheDict
    d = CacheDict(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["a"]
    d["d"] = 4
    assert len(d) == 3
    assert 'a' in d and 'c' in d and 'd' in d and 'b' not in d


def test_call():
    from jinja import Environment
    env = Environment()
    env.globals['foo'] = lambda a, b, c, e, g: a + b + c + e + g
    tmpl = env.from_string(CALL)
    assert tmpl.render() == 'abdfh'


def test_stringfilter(env):
    from jinja.filters import stringfilter
    f = stringfilter(lambda f, x: f + x)
    assert f('42')(env, None, 23) == '2342'


def test_simplefilter(env):
    from jinja.filters import simplefilter
    f = simplefilter(lambda f, x: f + x)
    assert f(42)(env, None, 23) == 65
