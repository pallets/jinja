import pytest
import asyncio

from jinja2 import Template, Environment, DictLoader
from jinja2.utils import have_async_gen
from jinja2.exceptions import TemplateNotFound, TemplatesNotFound


def run(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_basic_async():
    t = Template('{% for item in [1, 2, 3] %}[{{ item }}]{% endfor %}',
                 enable_async=True)
    async def func():
        return await t.render_async()

    rv = run(func())
    assert rv == '[1][2][3]'


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_await_on_calls():
    t = Template('{{ async_func() + normal_func() }}',
                 enable_async=True)

    async def async_func():
        return 42

    def normal_func():
        return 23

    async def func():
        return await t.render_async(
            async_func=async_func,
            normal_func=normal_func
        )

    rv = run(func())
    assert rv == '65'


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_await_on_calls_normal_render():
    t = Template('{{ async_func() + normal_func() }}',
                 enable_async=True)

    async def async_func():
        return 42

    def normal_func():
        return 23

    rv = t.render(
        async_func=async_func,
        normal_func=normal_func
    )

    assert rv == '65'


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_await_and_macros():
    t = Template('{% macro foo(x) %}[{{ x }}][{{ async_func() }}]'
                 '{% endmacro %}{{ foo(42) }}', enable_async=True)

    async def async_func():
        return 42

    async def func():
        return await t.render_async(async_func=async_func)

    rv = run(func())
    assert rv == '[42][42]'


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_async_blocks():
    t = Template('{% block foo %}<Test>{% endblock %}{{ self.foo() }}',
                 enable_async=True, autoescape=True)
    async def func():
        return await t.render_async()

    rv = run(func())
    assert rv == '<Test><Test>'


@pytest.fixture
def test_env_async():
    env = Environment(loader=DictLoader(dict(
        module='{% macro test() %}[{{ foo }}|{{ bar }}]{% endmacro %}',
        header='[{{ foo }}|{{ 23 }}]',
        o_printer='({{ o }})'
    )), enable_async=True)
    env.globals['bar'] = 23
    return env


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
@pytest.mark.imports
class TestAsyncImports(object):

    def test_context_imports(self, test_env_async):
        t = test_env_async.from_string('{% import "module" as m %}{{ m.test() }}')
        assert t.render(foo=42) == '[|23]'
        t = test_env_async.from_string(
            '{% import "module" as m without context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == '[|23]'
        t = test_env_async.from_string(
            '{% import "module" as m with context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == '[42|23]'
        t = test_env_async.from_string('{% from "module" import test %}{{ test() }}')
        assert t.render(foo=42) == '[|23]'
        t = test_env_async.from_string(
            '{% from "module" import test without context %}{{ test() }}'
        )
        assert t.render(foo=42) == '[|23]'
        t = test_env_async.from_string(
            '{% from "module" import test with context %}{{ test() }}'
        )
        assert t.render(foo=42) == '[42|23]'

    def test_trailing_comma(self, test_env_async):
        test_env_async.from_string('{% from "foo" import bar, baz with context %}')
        test_env_async.from_string('{% from "foo" import bar, baz, with context %}')
        test_env_async.from_string('{% from "foo" import bar, with context %}')
        test_env_async.from_string('{% from "foo" import bar, with, context %}')
        test_env_async.from_string('{% from "foo" import bar, with with context %}')

    def test_exports(self, test_env_async):
        m = run(test_env_async.from_string('''
            {% macro toplevel() %}...{% endmacro %}
            {% macro __private() %}...{% endmacro %}
            {% set variable = 42 %}
            {% for item in [1] %}
                {% macro notthere() %}{% endmacro %}
            {% endfor %}
        ''')._get_default_module_async())
        assert run(m.toplevel()) == '...'
        assert not hasattr(m, '__missing')
        assert m.variable == 42
        assert not hasattr(m, 'notthere')


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
@pytest.mark.imports
@pytest.mark.includes
class TestAsyncIncludes(object):

    def test_context_include(self, test_env_async):
        t = test_env_async.from_string('{% include "header" %}')
        assert t.render(foo=42) == '[42|23]'
        t = test_env_async.from_string('{% include "header" with context %}')
        assert t.render(foo=42) == '[42|23]'
        t = test_env_async.from_string('{% include "header" without context %}')
        assert t.render(foo=42) == '[|23]'

    def test_choice_includes(self, test_env_async):
        t = test_env_async.from_string('{% include ["missing", "header"] %}')
        assert t.render(foo=42) == '[42|23]'

        t = test_env_async.from_string(
            '{% include ["missing", "missing2"] ignore missing %}'
        )
        assert t.render(foo=42) == ''

        t = test_env_async.from_string('{% include ["missing", "missing2"] %}')
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

        t = test_env_async.from_string('{% include ["missing", "header"] %}')
        test_includes(t)
        t = test_env_async.from_string('{% include x %}')
        test_includes(t, x=['missing', 'header'])
        t = test_env_async.from_string('{% include [x, "header"] %}')
        test_includes(t, x='missing')
        t = test_env_async.from_string('{% include x %}')
        test_includes(t, x='header')
        t = test_env_async.from_string('{% include x %}')
        test_includes(t, x='header')
        t = test_env_async.from_string('{% include [x] %}')
        test_includes(t, x='header')

    def test_include_ignoring_missing(self, test_env_async):
        t = test_env_async.from_string('{% include "missing" %}')
        pytest.raises(TemplateNotFound, t.render)
        for extra in '', 'with context', 'without context':
            t = test_env_async.from_string('{% include "missing" ignore missing ' +
                                     extra + ' %}')
            assert t.render() == ''

    def test_context_include_with_overrides(self, test_env_async):
        env = Environment(loader=DictLoader(dict(
            main="{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}",
            item="{{ item }}"
        )))
        assert env.get_template("main").render() == "123"

    def test_unoptimized_scopes(self, test_env_async):
        t = test_env_async.from_string("""
            {% macro outer(o) %}
            {% macro inner() %}
            {% include "o_printer" %}
            {% endmacro %}
            {{ inner() }}
            {% endmacro %}
            {{ outer("FOO") }}
        """)
        assert t.render().strip() == '(FOO)'
