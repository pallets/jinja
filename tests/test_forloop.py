# -*- coding: utf-8 -*-
"""
    unit test for loop functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment
from jinja2.exceptions import UndefinedError, TemplateSyntaxError

from nose.tools import assert_raises

env = Environment()


SIMPLE = '''{% for item in seq %}{{ item }}{% endfor %}'''
ELSE = '''{% for item in seq %}XXX{% else %}...{% endfor %}'''
EMPTYBLOCKS = '''<{% for item in seq %}{% else %}{% endfor %}>'''
CONTEXTVARS = '''{% for item in seq %}\
{{ loop.index }}|{{ loop.index0 }}|{{ loop.revindex }}|{{
   loop.revindex0 }}|{{ loop.first }}|{{ loop.last }}|{{
   loop.length }}###{% endfor %}'''
CYCLING = '''{% for item in seq %}{{ loop.cycle('<1>', '<2>') }}{% endfor %}\
{% for item in seq %}{{ loop.cycle(*through) }}{% endfor %}'''
SCOPE = '''{% for item in seq %}{% endfor %}{{ item }}'''
VARLEN = '''{% for item in iter %}{{ item }}{% endfor %}'''
NONITER = '''{% for item in none %}...{% endfor %}'''
RECURSIVE = '''{% for item in seq recursive -%}
    [{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
{%- endfor %}'''
LOOPLOOP = '''{% for row in table %}
    {%- set rowloop = loop -%}
    {% for cell in row -%}
        [{{ rowloop.index }}|{{ loop.index }}]
    {%- endfor %}
{%- endfor %}'''
LOOPERROR1 = '''\
{% for item in [1] if loop.index == 0 %}...{% endfor %}'''
LOOPERROR2 = '''\
{% for item in [] %}...{% else %}{{ loop }}{% endfor %}'''
LOOPFILTER = '''\
{% for item in range(10) if item is even %}[{{ item }}]{% endfor %}'''
EXTENDEDLOOPFILTER = '''\
{% for item in range(10) if item is even %}[{{ loop.index
}}:{{ item }}]{% endfor %}'''
LOOPUNASSIGNABLE = '''\
{% for loop in seq %}...{% endfor %}'''


def test_simple():
    tmpl = env.from_string(SIMPLE)
    assert tmpl.render(seq=range(10)) == '0123456789'


def test_else():
    tmpl = env.from_string(ELSE)
    assert tmpl.render() == '...'


def test_empty_blocks():
    tmpl = env.from_string(EMPTYBLOCKS)
    assert tmpl.render() == '<>'


def test_context_vars():
    tmpl = env.from_string(CONTEXTVARS)
    one, two, _ = tmpl.render(seq=[0, 1]).split('###')
    (one_index, one_index0, one_revindex, one_revindex0, one_first,
     one_last, one_length) = one.split('|')
    (two_index, two_index0, two_revindex, two_revindex0, two_first,
     two_last, two_length) = two.split('|')

    assert int(one_index) == 1 and int(two_index) == 2
    assert int(one_index0) == 0 and int(two_index0) == 1
    assert int(one_revindex) == 2 and int(two_revindex) == 1
    assert int(one_revindex0) == 1 and int(two_revindex0) == 0
    assert one_first == 'True' and two_first == 'False'
    assert one_last == 'False' and two_last == 'True'
    assert one_length == two_length == '2'


def test_cycling():
    tmpl = env.from_string(CYCLING)
    output = tmpl.render(seq=range(4), through=('<1>', '<2>'))
    assert output == '<1><2>' * 4


def test_scope():
    tmpl = env.from_string(SCOPE)
    output = tmpl.render(seq=range(10))
    assert not output


def test_varlen():
    def inner():
        for item in range(5):
            yield item
    tmpl = env.from_string(VARLEN)
    output = tmpl.render(iter=inner())
    assert output == '01234'


def test_noniter():
    tmpl = env.from_string(NONITER)
    assert_raises(TypeError, tmpl.render)


def test_recursive():
    tmpl = env.from_string(RECURSIVE)
    assert tmpl.render(seq=[
        dict(a=1, b=[dict(a=1), dict(a=2)]),
        dict(a=2, b=[dict(a=1), dict(a=2)]),
        dict(a=3, b=[dict(a='a')])
    ]) == '[1<[1][2]>][2<[1][2]>][3<[a]>]'


def test_looploop():
    tmpl = env.from_string(LOOPLOOP)
    assert tmpl.render(table=['ab', 'cd']) == '[1|1][1|2][2|1][2|2]'


def test_reversed_bug():
    tmpl = env.from_string('{% for i in items %}{{ i }}{% if not loop.last %}'
                           ',{% endif %}{% endfor %}')
    assert tmpl.render(items=reversed([3, 2, 1])) == '1,2,3'


def test_loop_errors():
    tmpl = env.from_string(LOOPERROR1)
    assert_raises(UndefinedError, tmpl.render)
    tmpl = env.from_string(LOOPERROR2)
    assert tmpl.render() == ''


def test_loop_filter():
    tmpl = env.from_string(LOOPFILTER)
    assert tmpl.render() == '[0][2][4][6][8]'
    tmpl = env.from_string(EXTENDEDLOOPFILTER)
    assert tmpl.render() == '[1:0][2:2][3:4][4:6][5:8]'


def test_loop_unassignable():
    assert_raises(TemplateSyntaxError, env.from_string, LOOPUNASSIGNABLE)


def test_scoped_special_var():
    t = env.from_string('{% for s in seq %}[{{ loop.first }}{% for c in s %}'
                        '|{{ loop.first }}{% endfor %}]{% endfor %}')
    assert t.render(seq=('ab', 'cd')) == '[True|True|False][False|True|False]'


def test_scoped_loop_var():
    t = env.from_string('{% for x in seq %}{{ loop.first }}'
                        '{% for y in seq %}{% endfor %}{% endfor %}')
    assert t.render(seq='ab') == 'TrueFalse'
    t = env.from_string('{% for x in seq %}{% for y in seq %}'
                        '{{ loop.first }}{% endfor %}{% endfor %}')
    assert t.render(seq='ab') == 'TrueFalseTrueFalse'


def test_recursive_empty_loop_iter():
    t = env.from_string('''
    {%- for item in foo recursive -%}{%- endfor -%}
    ''')
    assert t.render(dict(foo=[])) == ''


def test_call_in_loop():
    t = env.from_string('''
    {%- macro do_something() -%}
        [{{ caller() }}]
    {%- endmacro %}

    {%- for i in [1, 2, 3] %}
        {%- call do_something() -%}
            {{ i }}
        {%- endcall %}
    {%- endfor -%}
    ''')
    assert t.render() == '[1][2][3]'


def test_scoping_bug():
    t = env.from_string('''
    {%- for item in foo %}...{{ item }}...{% endfor %}
    {%- macro item(a) %}...{{ a }}...{% endmacro %}
    {{- item(2) -}}
    ''')
    assert t.render(foo=(1,)) == '...1......2...'
