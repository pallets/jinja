# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.imports
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the import features (with includes).

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import pytest

from jinja2 import Environment, DictLoader
from jinja2.exceptions import TemplateNotFound, TemplatesNotFound


@pytest.fixture
def test_env():
    env = Environment(loader=DictLoader(dict(
        module='{% macro test() %}[{{ foo }}|{{ bar }}]{% endmacro %}',
        header='[{{ foo }}|{{ 23 }}]',
        o_printer='({{ o }})'
    )))
    env.globals['bar'] = 23
    return env


@pytest.mark.imports
class TestImports():

    def test_context_imports(self, test_env):
        t = test_env.from_string('{% import "module" as m %}{{ m.test() }}')
        assert t.render(foo=42) == '[|23]'
        t = test_env.from_string(
            '{% import "module" as m without context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == '[|23]'
        t = test_env.from_string(
            '{% import "module" as m with context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == '[42|23]'
        t = test_env.from_string('{% from "module" import test %}{{ test() }}')
        assert t.render(foo=42) == '[|23]'
        t = test_env.from_string(
            '{% from "module" import test without context %}{{ test() }}'
        )
        assert t.render(foo=42) == '[|23]'
        t = test_env.from_string(
            '{% from "module" import test with context %}{{ test() }}'
        )
        assert t.render(foo=42) == '[42|23]'

    def test_trailing_comma(self, test_env):
        test_env.from_string('{% from "foo" import bar, baz with context %}')
        test_env.from_string('{% from "foo" import bar, baz, with context %}')
        test_env.from_string('{% from "foo" import bar, with context %}')
        test_env.from_string('{% from "foo" import bar, with, context %}')
        test_env.from_string('{% from "foo" import bar, with with context %}')

    def test_exports(self, test_env):
        m = test_env.from_string('''
            {% macro toplevel() %}...{% endmacro %}
            {% macro __private() %}...{% endmacro %}
            {% set variable = 42 %}
            {% for item in [1] %}
                {% macro notthere() %}{% endmacro %}
            {% endfor %}
        ''').module
        assert m.toplevel() == '...'
        assert not hasattr(m, '__missing')
        assert m.variable == 42
        assert not hasattr(m, 'notthere')
        

@pytest.mark.imports
@pytest.mark.includes
class TestIncludes():

    def test_context_include(self, test_env):
        t = test_env.from_string('{% include "header" %}')
        assert t.render(foo=42) == '[42|23]'
        t = test_env.from_string('{% include "header" with context %}')
        assert t.render(foo=42) == '[42|23]'
        t = test_env.from_string('{% include "header" without context %}')
        assert t.render(foo=42) == '[|23]'

    def test_choice_includes(self, test_env):
        t = test_env.from_string('{% include ["missing", "header"] %}')
        assert t.render(foo=42) == '[42|23]'

        t = test_env.from_string(
            '{% include ["missing", "missing2"] ignore missing %}'
        )
        assert t.render(foo=42) == ''

        t = test_env.from_string('{% include ["missing", "missing2"] %}')
        pytest.raises(TemplateNotFound, t.render)
        try:
            t.render()
        except TemplatesNotFound as e:
            assert e.templates == ['missing', 'missing2']
            assert e.name == 'missing2'
        else:
            assert False, 'thou shalt raise'

        def test_includes(t, **ctx):
            ctx['foo'] = 42
            assert t.render(ctx) == '[42|23]'

        t = test_env.from_string('{% include ["missing", "header"] %}')
        test_includes(t)
        t = test_env.from_string('{% include x %}')
        test_includes(t, x=['missing', 'header'])
        t = test_env.from_string('{% include [x, "header"] %}')
        test_includes(t, x='missing')
        t = test_env.from_string('{% include x %}')
        test_includes(t, x='header')
        t = test_env.from_string('{% include x %}')
        test_includes(t, x='header')
        t = test_env.from_string('{% include [x] %}')
        test_includes(t, x='header')

    def test_include_ignoring_missing(self, test_env):
        t = test_env.from_string('{% include "missing" %}')
        pytest.raises(TemplateNotFound, t.render)
        for extra in '', 'with context', 'without context':
            t = test_env.from_string('{% include "missing" ignore missing ' +
                                     extra + ' %}')
            assert t.render() == ''

    def test_context_include_with_overrides(self, test_env):
        env = Environment(loader=DictLoader(dict(
            main="{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}",
            item="{{ item }}"
        )))
        assert env.get_template("main").render() == "123"

    def test_unoptimized_scopes(self, test_env):
        t = test_env.from_string("""
            {% macro outer(o) %}
            {% macro inner() %}
            {% include "o_printer" %}
            {% endmacro %}
            {{ inner() }}
            {% endmacro %}
            {{ outer("FOO") }}
        """)
        assert t.render().strip() == '(FOO)'

    def test_include_with(self, test_env):

        tmpl = test_env.from_string("{{ foo }}")
        t = test_env.from_string("{% set foo = 'bar' %}{% include tmpl %}")
        assert t.render({"tmpl":tmpl}).strip() == "bar"

        t = test_env.from_string("{% include tmpl with { 'foo' : 'BIZ' } %}")
        assert t.render({"tmpl":tmpl}).strip() == "BIZ"

        t = test_env.from_string("{% set foo = 'bar' %}{% include tmpl only %}")
        assert t.render({"tmpl":tmpl}).strip() == ""

        tmpl = test_env.from_string("{{ from_with }} {{ from_context }}")
        t = test_env.from_string("{% set from_context = 'CONTEXT' %}" +
                                 "{% include tmpl with { 'from_with' : 'WITH' } %}")
        assert t.render({"tmpl":tmpl}).strip() == "WITH CONTEXT"
        
        tmpl = test_env.from_string("{{ from_with }} {{ from_context }}")
        t = test_env.from_string("{% set from_context = 'CONTEXT' %}" +
                                 "{% include tmpl with { 'from_with' : 'WITH' } only %}")
        assert t.render({"tmpl":tmpl}).strip() == "WITH"
        
        env = Environment(loader=DictLoader(dict(
            inner="{{ global_var }} {{ arg }} {{ global_func(22) }}",
            main1="{% include 'inner' with context %}",
            main2="{% include 'inner' without context %}",
            main3="{% include 'inner' with { 'arg' : 43 } %}",
            main4="{% include 'inner' with { 'arg' : 43 } only %}",
            main5="{% include ['outer', 'inner'] with { 'arg' : 43 } only %}",
            main6="{% include 'inner' ignore missing with { 'arg' : 43 } only %}",
            main7="{% include 'outer' ignore missing with { 'arg' : 43 } only %}"
        )))
        env.globals['global_var'] = 42
        env.globals['global_func'] = lambda x: x * 2

        assert env.get_template("inner").render() == "42  44"
        assert env.get_template("main1").render() == "42  44"
        assert env.get_template("main2").render() == "42  44"
        assert env.get_template("main3").render() == "42 43 44"
        assert env.get_template("main4").render() == "42 43 44"
        assert env.get_template("main5").render() == "42 43 44"
        assert env.get_template("main6").render() == "42 43 44"
        assert env.get_template("main7").render() == ""
        
