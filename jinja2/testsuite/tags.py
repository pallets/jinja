# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.tags
    ~~~~~~~~~~~~~~~~~~~~~

    Test for most of the builtin tags.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import re
import unittest

from jinja2.testsuite import JinjaTestCase

from jinja2 import Environment, TemplateSyntaxError, UndefinedError

env = Environment()


class ForLoopTestCase(JinjaTestCase):

    def test_simple(self):
        tmpl = env.from_string('{% for item in seq %}{{ item }}{% endfor %}')
        assert tmpl.render(seq=range(10)) == '0123456789'

    def test_else(self):
        tmpl = env.from_string('{% for item in seq %}XXX{% else %}...{% endfor %}')
        assert tmpl.render() == '...'

    def test_empty_blocks(self):
        tmpl = env.from_string('<{% for item in seq %}{% else %}{% endfor %}>')
        assert tmpl.render() == '<>'

    def test_context_vars(self):
        tmpl = env.from_string('''{% for item in seq -%}
        {{ loop.index }}|{{ loop.index0 }}|{{ loop.revindex }}|{{
            loop.revindex0 }}|{{ loop.first }}|{{ loop.last }}|{{
           loop.length }}###{% endfor %}''')
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

    def test_cycling(self):
        tmpl = env.from_string('''{% for item in seq %}{{
            loop.cycle('<1>', '<2>') }}{% endfor %}{%
            for item in seq %}{{ loop.cycle(*through) }}{% endfor %}''')
        output = tmpl.render(seq=range(4), through=('<1>', '<2>'))
        assert output == '<1><2>' * 4

    def test_scope(self):
        tmpl = env.from_string('{% for item in seq %}{% endfor %}{{ item }}')
        output = tmpl.render(seq=range(10))
        assert not output

    def test_varlen(self):
        def inner():
            for item in range(5):
                yield item
        tmpl = env.from_string('{% for item in iter %}{{ item }}{% endfor %}')
        output = tmpl.render(iter=inner())
        assert output == '01234'

    def test_noniter(self):
        tmpl = env.from_string('{% for item in none %}...{% endfor %}')
        self.assert_raises(TypeError, tmpl.render)

    def test_recursive(self):
        tmpl = env.from_string('''{% for item in seq recursive -%}
            [{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}''')
        assert tmpl.render(seq=[
            dict(a=1, b=[dict(a=1), dict(a=2)]),
            dict(a=2, b=[dict(a=1), dict(a=2)]),
            dict(a=3, b=[dict(a='a')])
        ]) == '[1<[1][2]>][2<[1][2]>][3<[a]>]'

    def test_looploop(self):
        tmpl = env.from_string('''{% for row in table %}
            {%- set rowloop = loop -%}
            {% for cell in row -%}
                [{{ rowloop.index }}|{{ loop.index }}]
            {%- endfor %}
        {%- endfor %}''')
        assert tmpl.render(table=['ab', 'cd']) == '[1|1][1|2][2|1][2|2]'

    def test_reversed_bug(self):
        tmpl = env.from_string('{% for i in items %}{{ i }}'
                               '{% if not loop.last %}'
                               ',{% endif %}{% endfor %}')
        assert tmpl.render(items=reversed([3, 2, 1])) == '1,2,3'

    def test_loop_errors(self):
        tmpl = env.from_string('''{% for item in [1] if loop.index
                                      == 0 %}...{% endfor %}''')
        self.assert_raises(UndefinedError, tmpl.render)
        tmpl = env.from_string('''{% for item in [] %}...{% else
            %}{{ loop }}{% endfor %}''')
        assert tmpl.render() == ''

    def test_loop_filter(self):
        tmpl = env.from_string('{% for item in range(10) if item '
                               'is even %}[{{ item }}]{% endfor %}')
        assert tmpl.render() == '[0][2][4][6][8]'
        tmpl = env.from_string('''
            {%- for item in range(10) if item is even %}[{{
                loop.index }}:{{ item }}]{% endfor %}''')
        assert tmpl.render() == '[1:0][2:2][3:4][4:6][5:8]'

    def test_loop_unassignable(self):
        self.assert_raises(TemplateSyntaxError, env.from_string,
                           '{% for loop in seq %}...{% endfor %}')

    def test_scoped_special_var(self):
        t = env.from_string('{% for s in seq %}[{{ loop.first }}{% for c in s %}'
                            '|{{ loop.first }}{% endfor %}]{% endfor %}')
        assert t.render(seq=('ab', 'cd')) == '[True|True|False][False|True|False]'

    def test_scoped_loop_var(self):
        t = env.from_string('{% for x in seq %}{{ loop.first }}'
                            '{% for y in seq %}{% endfor %}{% endfor %}')
        assert t.render(seq='ab') == 'TrueFalse'
        t = env.from_string('{% for x in seq %}{% for y in seq %}'
                            '{{ loop.first }}{% endfor %}{% endfor %}')
        assert t.render(seq='ab') == 'TrueFalseTrueFalse'

    def test_recursive_empty_loop_iter(self):
        t = env.from_string('''
        {%- for item in foo recursive -%}{%- endfor -%}
        ''')
        assert t.render(dict(foo=[])) == ''

    def test_call_in_loop(self):
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

    def test_scoping_bug(self):
        t = env.from_string('''
        {%- for item in foo %}...{{ item }}...{% endfor %}
        {%- macro item(a) %}...{{ a }}...{% endmacro %}
        {{- item(2) -}}
        ''')
        assert t.render(foo=(1,)) == '...1......2...'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ForLoopTestCase))
    return suite
