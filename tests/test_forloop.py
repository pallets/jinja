# -*- coding: utf-8 -*-
"""
    unit test for loop functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

SIMPLE = '''{% for item in seq %}{{ item }}{% endfor %}'''
ELSE = '''{% for item in seq %}XXX{% else %}...{% endfor %}'''
EMPTYBLOCKS = '''<{% for item in seq %}{% else %}{% endfor %}>'''
CONTEXTVARS = '''{% for item in seq %}\
{{ loop.index }}|{{ loop.index0 }}|{{ loop.revindex }}|{{
   loop.revindex0 }}|{{ loop.first }}|{{ loop.last }}|{{
   loop.even }}|{{ loop.odd }}|{{ loop.length }}###{% endfor %}'''
CYCLING = '''{% for item in seq %}{% cycle '<1>', '<2>' %}{% endfor %}\
{% for item in seq %}{% cycle through %}{% endfor %}'''
SCOPE = '''{% for item in seq %}{% endfor %}{{ item }}'''
VARLEN = '''{% for item in iter %}{{ item }}{% endfor %}'''


def test_simple(env):
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render(seq=range(10)) == '0123456789'


def test_else(env):
    tmpl = env.from_string(ELSE)
    assert tmpl.render() == '...'


def test_empty_blocks(env):
    tmpl = env.from_string(EMPTYBLOCKS)
    assert tmpl.render() == '<>'


def test_context_vars(env):
    tmpl = env.from_string(CONTEXTVARS)
    one, two, _ = tmpl.render(seq=[0, 1]).split('###')
    (one_index, one_index0, one_revindex, one_revindex0, one_first,
     one_last, one_even, one_odd, one_length) = one.split('|')
    (two_index, two_index0, two_revindex, two_revindex0, two_first,
     two_last, two_even, two_odd, two_length) = two.split('|')

    assert int(one_index) == 1 and int(two_index) == 2
    assert int(one_index0) == 0 and int(two_index0) == 1
    assert int(one_revindex) == 2 and int(two_revindex) == 1
    assert int(one_revindex0) == 1 and int(two_revindex0) == 0
    assert one_first == 'True' and two_first == 'False'
    assert one_last == 'False' and two_last == 'True'
    assert one_even == 'False' and two_even == 'True'
    assert one_odd == 'True' and two_odd == 'False'
    assert one_length == two_length == '2'


def test_cycling(env):
    tmpl = env.from_string(CYCLING)
    output = tmpl.render(seq=range(4), through=('<1>', '<2>'))
    assert output == '<1><2>' * 4


def test_scope(env):
    tmpl = env.from_string(SCOPE)
    output = tmpl.render(seq=range(10))
    assert not output


def test_varlen(env):
    def inner():
        for item in range(5):
            yield item
    tmpl = env.from_string(VARLEN)
    output = tmpl.render(iter=inner())
    assert output == '01234'
