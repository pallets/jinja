# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.regression
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests corner cases and bugs.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import pytest

from jinja2 import Template, Environment, DictLoader, TemplateSyntaxError, \
     TemplateNotFound, PrefixLoader
from jinja2._compat import text_type


@pytest.mark.regression
class TestCorner(object):

    def test_assigned_scoping(self, env):
        t = env.from_string('''
        {%- for item in (1, 2, 3, 4) -%}
            [{{ item }}]
        {%- endfor %}
        {{- item -}}
        ''')
        assert t.render(item=42) == '[1][2][3][4]42'

        t = env.from_string('''
        {%- for item in (1, 2, 3, 4) -%}
            [{{ item }}]
        {%- endfor %}
        {%- set item = 42 %}
        {{- item -}}
        ''')
        assert t.render() == '[1][2][3][4]42'

        t = env.from_string('''
        {%- set item = 42 %}
        {%- for item in (1, 2, 3, 4) -%}
            [{{ item }}]
        {%- endfor %}
        {{- item -}}
        ''')
        assert t.render() == '[1][2][3][4]42'

    def test_closure_scoping(self, env):
        t = env.from_string('''
        {%- set wrapper = "<FOO>" %}
        {%- for item in (1, 2, 3, 4) %}
            {%- macro wrapper() %}[{{ item }}]{% endmacro %}
            {{- wrapper() }}
        {%- endfor %}
        {{- wrapper -}}
        ''')
        assert t.render() == '[1][2][3][4]<FOO>'

        t = env.from_string('''
        {%- for item in (1, 2, 3, 4) %}
            {%- macro wrapper() %}[{{ item }}]{% endmacro %}
            {{- wrapper() }}
        {%- endfor %}
        {%- set wrapper = "<FOO>" %}
        {{- wrapper -}}
        ''')
        assert t.render() == '[1][2][3][4]<FOO>'

        t = env.from_string('''
        {%- for item in (1, 2, 3, 4) %}
            {%- macro wrapper() %}[{{ item }}]{% endmacro %}
            {{- wrapper() }}
        {%- endfor %}
        {{- wrapper -}}
        ''')
        assert t.render(wrapper=23) == '[1][2][3][4]23'


@pytest.mark.regression
class TestBug(object):

    def test_keyword_folding(self, env):
        env = Environment()
        env.filters['testing'] = lambda value, some: value + some
        assert env.from_string("{{ 'test'|testing(some='stuff') }}") \
            .render() == 'teststuff'

    def test_extends_output_bugs(self, env):
        env = Environment(loader=DictLoader({
            'parent.html': '(({% block title %}{% endblock %}))'
        }))

        t = env.from_string(
            '{% if expr %}{% extends "parent.html" %}{% endif %}'
            '[[{% block title %}title{% endblock %}]]'
            '{% for item in [1, 2, 3] %}({{ item }}){% endfor %}'
        )
        assert t.render(expr=False) == '[[title]](1)(2)(3)'
        assert t.render(expr=True) == '((title))'

    def test_urlize_filter_escaping(self, env):
        tmpl = env.from_string('{{ "http://www.example.org/<foo"|urlize }}')
        assert tmpl.render() == '<a href="http://www.example.org/&lt;foo" rel="noopener">'\
            'http://www.example.org/&lt;foo</a>'

    def test_loop_call_loop(self, env):
        tmpl = env.from_string('''

        {% macro test() %}
            {{ caller() }}
        {% endmacro %}

        {% for num1 in range(5) %}
            {% call test() %}
                {% for num2 in range(10) %}
                    {{ loop.index }}
                {% endfor %}
            {% endcall %}
        {% endfor %}

        ''')

        assert tmpl.render().split() \
            == [text_type(x) for x in range(1, 11)] * 5

    def test_weird_inline_comment(self, env):
        env = Environment(line_statement_prefix='%')
        pytest.raises(TemplateSyntaxError, env.from_string,
                      '% for item in seq {# missing #}\n...% endfor')

    def test_old_macro_loop_scoping_bug(self, env):
        tmpl = env.from_string('{% for i in (1, 2) %}{{ i }}{% endfor %}'
                               '{% macro i() %}3{% endmacro %}{{ i() }}')
        assert tmpl.render() == '123'

    def test_partial_conditional_assignments(self, env):
        tmpl = env.from_string('{% if b %}{% set a = 42 %}{% endif %}{{ a }}')
        assert tmpl.render(a=23) == '23'
        assert tmpl.render(b=True) == '42'

    def test_stacked_locals_scoping_bug(self, env):
        env = Environment(line_statement_prefix='#')
        t = env.from_string('''\
# for j in [1, 2]:
#   set x = 1
#   for i in [1, 2]:
#     print x
#     if i % 2 == 0:
#       set x = x + 1
#     endif
#   endfor
# endfor
# if a
#   print 'A'
# elif b
#   print 'B'
# elif c == d
#   print 'C'
# else
#   print 'D'
# endif
    ''')
        assert t.render(a=0, b=False, c=42, d=42.0) == '1111C'

    def test_stacked_locals_scoping_bug_twoframe(self, env):
        t = Template('''
            {% set x = 1 %}
            {% for item in foo %}
                {% if item == 1 %}
                    {% set x = 2 %}
                {% endif %}
            {% endfor %}
            {{ x }}
        ''')
        rv = t.render(foo=[1]).strip()
        assert rv == u'1'

    def test_call_with_args(self, env):
        t = Template("""{% macro dump_users(users) -%}
        <ul>
          {%- for user in users -%}
            <li><p>{{ user.username|e }}</p>{{ caller(user) }}</li>
          {%- endfor -%}
          </ul>
        {%- endmacro -%}

        {% call(user) dump_users(list_of_user) -%}
          <dl>
            <dl>Realname</dl>
            <dd>{{ user.realname|e }}</dd>
            <dl>Description</dl>
            <dd>{{ user.description }}</dd>
          </dl>
        {% endcall %}""")

        assert [x.strip() for x in t.render(list_of_user=[{
            'username': 'apo',
            'realname': 'something else',
            'description': 'test'
        }]).splitlines()] == [
            u'<ul><li><p>apo</p><dl>',
            u'<dl>Realname</dl>',
            u'<dd>something else</dd>',
            u'<dl>Description</dl>',
            u'<dd>test</dd>',
            u'</dl>',
            u'</li></ul>'
        ]

    def test_empty_if_condition_fails(self, env):
        pytest.raises(TemplateSyntaxError,
                      Template, '{% if %}....{% endif %}')
        pytest.raises(TemplateSyntaxError,
                      Template, '{% if foo %}...{% elif %}...{% endif %}')
        pytest.raises(TemplateSyntaxError,
                      Template, '{% for x in %}..{% endfor %}')

    def test_recursive_loop_bug(self, env):
        tpl1 = Template("""
        {% for p in foo recursive%}
            {{p.bar}}
            {% for f in p.fields recursive%}
                {{f.baz}}
                {{p.bar}}
                {% if f.rec %}
                    {{ loop(f.sub) }}
                {% endif %}
            {% endfor %}
        {% endfor %}
        """)

        tpl2 = Template("""
        {% for p in foo%}
            {{p.bar}}
            {% for f in p.fields recursive%}
                {{f.baz}}
                {{p.bar}}
                {% if f.rec %}
                    {{ loop(f.sub) }}
                {% endif %}
            {% endfor %}
        {% endfor %}
        """)

    def test_else_loop_bug(self, env):
        t = Template('''
            {% for x in y %}
                {{ loop.index0 }}
            {% else %}
                {% for i in range(3) %}{{ i }}{% endfor %}
            {% endfor %}
        ''')
        assert t.render(y=[]).strip() == '012'

    def test_correct_prefix_loader_name(self, env):
        env = Environment(loader=PrefixLoader({
            'foo':  DictLoader({})
        }))
        try:
            env.get_template('foo/bar.html')
        except TemplateNotFound as e:
            assert e.name == 'foo/bar.html'
        else:
            assert False, 'expected error here'

    def test_contextfunction_callable_classes(self, env):
        from jinja2.utils import contextfunction

        class CallableClass(object):
            @contextfunction
            def __call__(self, ctx):
                return ctx.resolve('hello')

        tpl = Template("""{{ callableclass() }}""")
        output = tpl.render(callableclass=CallableClass(), hello='TEST')
        expected = 'TEST'

        assert output == expected

    @pytest.mark.skipif(sys.version_info[0] > 2,
                        reason='This only works on 2.x')
    def test_old_style_attribute(self, env):
        class Foo:
            x = 42
        assert env.getitem(Foo(), 'x') == 42

    def test_block_set_with_extends(self):
        env = Environment(loader=DictLoader({
            'main': '{% block body %}[{{ x }}]{% endblock %}',
        }))
        t = env.from_string('{% extends "main" %}{% set x %}42{% endset %}')
        assert t.render() == '[42]'

    def test_nested_for_else(self, env):
        tmpl = env.from_string('{% for x in y %}{{ loop.index0 }}{% else %}'
                               '{% for i in range(3) %}{{ i }}{% endfor %}'
                               '{% endfor %}')
        assert tmpl.render() == '012'

    def test_macro_var_bug(self, env):
        tmpl = env.from_string('''
        {% set i = 1 %}
        {% macro test() %}
            {% for i in range(0, 10) %}{{ i }}{% endfor %}
        {% endmacro %}{{ test() }}
        ''')
        assert tmpl.render().strip() == '0123456789'

    def test_macro_var_bug_advanced(self, env):
        tmpl = env.from_string('''
        {% macro outer() %}
            {% set i = 1 %}
            {% macro test() %}
                {% for i in range(0, 10) %}{{ i }}{% endfor %}
            {% endmacro %}{{ test() }}
        {% endmacro %}{{ outer() }}
        ''')
        assert tmpl.render().strip() == '0123456789'

    def test_callable_defaults(self):
        env = Environment()
        env.globals['get_int'] = lambda: 42
        t = env.from_string('''
        {% macro test(a, b, c=get_int()) -%}
             {{ a + b + c }}
        {%- endmacro %}
        {{ test(1, 2) }}|{{ test(1, 2, 3) }}
        ''')
        assert t.render().strip() == '45|6'

    def test_macro_escaping(self):
        env = Environment(
            autoescape=lambda x: False, extensions=['jinja2.ext.autoescape'])
        template = "{% macro m() %}<html>{% endmacro %}"
        template += "{% autoescape true %}{{ m() }}{% endautoescape %}"
        assert env.from_string(template).render()

    def test_macro_scoping(self, env):
        tmpl = env.from_string('''
        {% set n=[1,2,3,4,5] %}
        {% for n in [[1,2,3], [3,4,5], [5,6,7]] %}

        {% macro x(l) %}
          {{ l.pop() }}
          {% if l %}{{ x(l) }}{% endif %}
        {% endmacro %}

        {{ x(n) }}

        {% endfor %}
        ''')
        assert list(map(int, tmpl.render().split())) == \
            [3, 2, 1, 5, 4, 3, 7, 6, 5]

    def test_scopes_and_blocks(self):
        env = Environment(loader=DictLoader({
            'a.html': '''
                {%- set foo = 'bar' -%}
                {% include 'x.html' -%}
            ''',
            'b.html': '''
                {%- set foo = 'bar' -%}
                {% block test %}{% include 'x.html' %}{% endblock -%}
                ''',
            'c.html': '''
                {%- set foo = 'bar' -%}
                {% block test %}{% set foo = foo
                    %}{% include 'x.html' %}{% endblock -%}
            ''',
            'x.html': '''{{ foo }}|{{ test }}'''
        }))

        a = env.get_template('a.html')
        b = env.get_template('b.html')
        c = env.get_template('c.html')

        assert a.render(test='x').strip() == 'bar|x'
        assert b.render(test='x').strip() == 'bar|x'
        assert c.render(test='x').strip() == 'bar|x'

    def test_scopes_and_include(self):
        env = Environment(loader=DictLoader({
            'include.html': '{{ var }}',
            'base.html': '{% include "include.html" %}',
            'child.html': '{% extends "base.html" %}{% set var = 42 %}',
        }))
        t = env.get_template('child.html')
        assert t.render() == '42'
