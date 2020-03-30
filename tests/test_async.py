import asyncio

import pytest

from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import Template
from jinja2.asyncsupport import auto_aiter
from jinja2.exceptions import TemplateNotFound
from jinja2.exceptions import TemplatesNotFound
from jinja2.exceptions import UndefinedError


def run(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


def test_basic_async():
    t = Template(
        "{% for item in [1, 2, 3] %}[{{ item }}]{% endfor %}", enable_async=True
    )

    async def func():
        return await t.render_async()

    rv = run(func())
    assert rv == "[1][2][3]"


def test_await_on_calls():
    t = Template("{{ async_func() + normal_func() }}", enable_async=True)

    async def async_func():
        return 42

    def normal_func():
        return 23

    async def func():
        return await t.render_async(async_func=async_func, normal_func=normal_func)

    rv = run(func())
    assert rv == "65"


def test_await_on_calls_normal_render():
    t = Template("{{ async_func() + normal_func() }}", enable_async=True)

    async def async_func():
        return 42

    def normal_func():
        return 23

    rv = t.render(async_func=async_func, normal_func=normal_func)

    assert rv == "65"


def test_await_and_macros():
    t = Template(
        "{% macro foo(x) %}[{{ x }}][{{ async_func() }}]{% endmacro %}{{ foo(42) }}",
        enable_async=True,
    )

    async def async_func():
        return 42

    async def func():
        return await t.render_async(async_func=async_func)

    rv = run(func())
    assert rv == "[42][42]"


def test_async_blocks():
    t = Template(
        "{% block foo %}<Test>{% endblock %}{{ self.foo() }}",
        enable_async=True,
        autoescape=True,
    )

    async def func():
        return await t.render_async()

    rv = run(func())
    assert rv == "<Test><Test>"


def test_async_generate():
    t = Template("{% for x in [1, 2, 3] %}{{ x }}{% endfor %}", enable_async=True)
    rv = list(t.generate())
    assert rv == ["1", "2", "3"]


def test_async_iteration_in_templates():
    t = Template("{% for x in rng %}{{ x }}{% endfor %}", enable_async=True)

    async def async_iterator():
        for item in [1, 2, 3]:
            yield item

    rv = list(t.generate(rng=async_iterator()))
    assert rv == ["1", "2", "3"]


def test_async_iteration_in_templates_extended():
    t = Template(
        "{% for x in rng %}{{ loop.index0 }}/{{ x }}{% endfor %}", enable_async=True
    )
    stream = t.generate(rng=auto_aiter(range(1, 4)))
    assert next(stream) == "0"
    assert "".join(stream) == "/11/22/3"


@pytest.fixture
def test_env_async():
    env = Environment(
        loader=DictLoader(
            dict(
                module="{% macro test() %}[{{ foo }}|{{ bar }}]{% endmacro %}",
                header="[{{ foo }}|{{ 23 }}]",
                o_printer="({{ o }})",
            )
        ),
        enable_async=True,
    )
    env.globals["bar"] = 23
    return env


class TestAsyncImports(object):
    def test_context_imports(self, test_env_async):
        t = test_env_async.from_string('{% import "module" as m %}{{ m.test() }}')
        assert t.render(foo=42) == "[|23]"
        t = test_env_async.from_string(
            '{% import "module" as m without context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == "[|23]"
        t = test_env_async.from_string(
            '{% import "module" as m with context %}{{ m.test() }}'
        )
        assert t.render(foo=42) == "[42|23]"
        t = test_env_async.from_string('{% from "module" import test %}{{ test() }}')
        assert t.render(foo=42) == "[|23]"
        t = test_env_async.from_string(
            '{% from "module" import test without context %}{{ test() }}'
        )
        assert t.render(foo=42) == "[|23]"
        t = test_env_async.from_string(
            '{% from "module" import test with context %}{{ test() }}'
        )
        assert t.render(foo=42) == "[42|23]"

    def test_trailing_comma(self, test_env_async):
        test_env_async.from_string('{% from "foo" import bar, baz with context %}')
        test_env_async.from_string('{% from "foo" import bar, baz, with context %}')
        test_env_async.from_string('{% from "foo" import bar, with context %}')
        test_env_async.from_string('{% from "foo" import bar, with, context %}')
        test_env_async.from_string('{% from "foo" import bar, with with context %}')

    def test_exports(self, test_env_async):
        m = run(
            test_env_async.from_string(
                """
            {% macro toplevel() %}...{% endmacro %}
            {% macro __private() %}...{% endmacro %}
            {% set variable = 42 %}
            {% for item in [1] %}
                {% macro notthere() %}{% endmacro %}
            {% endfor %}
        """
            )._get_default_module_async()
        )
        assert run(m.toplevel()) == "..."
        assert not hasattr(m, "__missing")
        assert m.variable == 42
        assert not hasattr(m, "notthere")


class TestAsyncIncludes(object):
    def test_context_include(self, test_env_async):
        t = test_env_async.from_string('{% include "header" %}')
        assert t.render(foo=42) == "[42|23]"
        t = test_env_async.from_string('{% include "header" with context %}')
        assert t.render(foo=42) == "[42|23]"
        t = test_env_async.from_string('{% include "header" without context %}')
        assert t.render(foo=42) == "[|23]"

    def test_choice_includes(self, test_env_async):
        t = test_env_async.from_string('{% include ["missing", "header"] %}')
        assert t.render(foo=42) == "[42|23]"

        t = test_env_async.from_string(
            '{% include ["missing", "missing2"] ignore missing %}'
        )
        assert t.render(foo=42) == ""

        t = test_env_async.from_string('{% include ["missing", "missing2"] %}')
        pytest.raises(TemplateNotFound, t.render)
        with pytest.raises(TemplatesNotFound) as e:
            t.render()

        assert e.value.templates == ["missing", "missing2"]
        assert e.value.name == "missing2"

        def test_includes(t, **ctx):
            ctx["foo"] = 42
            assert t.render(ctx) == "[42|23]"

        t = test_env_async.from_string('{% include ["missing", "header"] %}')
        test_includes(t)
        t = test_env_async.from_string("{% include x %}")
        test_includes(t, x=["missing", "header"])
        t = test_env_async.from_string('{% include [x, "header"] %}')
        test_includes(t, x="missing")
        t = test_env_async.from_string("{% include x %}")
        test_includes(t, x="header")
        t = test_env_async.from_string("{% include x %}")
        test_includes(t, x="header")
        t = test_env_async.from_string("{% include [x] %}")
        test_includes(t, x="header")

    def test_include_ignoring_missing(self, test_env_async):
        t = test_env_async.from_string('{% include "missing" %}')
        pytest.raises(TemplateNotFound, t.render)
        for extra in "", "with context", "without context":
            t = test_env_async.from_string(
                '{% include "missing" ignore missing ' + extra + " %}"
            )
            assert t.render() == ""

    def test_context_include_with_overrides(self, test_env_async):
        env = Environment(
            loader=DictLoader(
                dict(
                    main="{% for item in [1, 2, 3] %}{% include 'item' %}{% endfor %}",
                    item="{{ item }}",
                )
            )
        )
        assert env.get_template("main").render() == "123"

    def test_unoptimized_scopes(self, test_env_async):
        t = test_env_async.from_string(
            """
            {% macro outer(o) %}
            {% macro inner() %}
            {% include "o_printer" %}
            {% endmacro %}
            {{ inner() }}
            {% endmacro %}
            {{ outer("FOO") }}
        """
        )
        assert t.render().strip() == "(FOO)"

    def test_unoptimized_scopes_autoescape(self):
        env = Environment(
            loader=DictLoader(dict(o_printer="({{ o }})",)),
            autoescape=True,
            enable_async=True,
        )
        t = env.from_string(
            """
            {% macro outer(o) %}
            {% macro inner() %}
            {% include "o_printer" %}
            {% endmacro %}
            {{ inner() }}
            {% endmacro %}
            {{ outer("FOO") }}
        """
        )
        assert t.render().strip() == "(FOO)"


class TestAsyncForLoop(object):
    def test_simple(self, test_env_async):
        tmpl = test_env_async.from_string("{% for item in seq %}{{ item }}{% endfor %}")
        assert tmpl.render(seq=list(range(10))) == "0123456789"

    def test_else(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for item in seq %}XXX{% else %}...{% endfor %}"
        )
        assert tmpl.render() == "..."

    def test_empty_blocks(self, test_env_async):
        tmpl = test_env_async.from_string(
            "<{% for item in seq %}{% else %}{% endfor %}>"
        )
        assert tmpl.render() == "<>"

    @pytest.mark.parametrize(
        "transform", [lambda x: x, iter, reversed, lambda x: (i for i in x), auto_aiter]
    )
    def test_context_vars(self, test_env_async, transform):
        t = test_env_async.from_string(
            "{% for item in seq %}{{ loop.index }}|{{ loop.index0 }}"
            "|{{ loop.revindex }}|{{ loop.revindex0 }}|{{ loop.first }}"
            "|{{ loop.last }}|{{ loop.length }}\n{% endfor %}"
        )
        out = t.render(seq=transform([42, 24]))
        assert out == "1|0|2|1|True|False|2\n2|1|1|0|False|True|2\n"

    def test_cycling(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in seq %}{{
            loop.cycle('<1>', '<2>') }}{% endfor %}{%
            for item in seq %}{{ loop.cycle(*through) }}{% endfor %}"""
        )
        output = tmpl.render(seq=list(range(4)), through=("<1>", "<2>"))
        assert output == "<1><2>" * 4

    def test_lookaround(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in seq -%}
            {{ loop.previtem|default('x') }}-{{ item }}-{{
            loop.nextitem|default('x') }}|
        {%- endfor %}"""
        )
        output = tmpl.render(seq=list(range(4)))
        assert output == "x-0-1|0-1-2|1-2-3|2-3-x|"

    def test_changed(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in seq -%}
            {{ loop.changed(item) }},
        {%- endfor %}"""
        )
        output = tmpl.render(seq=[None, None, 1, 2, 2, 3, 4, 4, 4])
        assert output == "True,False,True,True,False,True,True,False,False,"

    def test_scope(self, test_env_async):
        tmpl = test_env_async.from_string("{% for item in seq %}{% endfor %}{{ item }}")
        output = tmpl.render(seq=list(range(10)))
        assert not output

    def test_varlen(self, test_env_async):
        def inner():
            for item in range(5):
                yield item

        tmpl = test_env_async.from_string(
            "{% for item in iter %}{{ item }}{% endfor %}"
        )
        output = tmpl.render(iter=inner())
        assert output == "01234"

    def test_noniter(self, test_env_async):
        tmpl = test_env_async.from_string("{% for item in none %}...{% endfor %}")
        pytest.raises(TypeError, tmpl.render)

    def test_recursive(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in seq recursive -%}
            [{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
        )
        assert (
            tmpl.render(
                seq=[
                    dict(a=1, b=[dict(a=1), dict(a=2)]),
                    dict(a=2, b=[dict(a=1), dict(a=2)]),
                    dict(a=3, b=[dict(a="a")]),
                ]
            )
            == "[1<[1][2]>][2<[1][2]>][3<[a]>]"
        )

    def test_recursive_lookaround(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in seq recursive -%}
            [{{ loop.previtem.a if loop.previtem is defined else 'x' }}.{{
            item.a }}.{{ loop.nextitem.a if loop.nextitem is defined else 'x'
            }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
        {%- endfor %}"""
        )
        assert (
            tmpl.render(
                seq=[
                    dict(a=1, b=[dict(a=1), dict(a=2)]),
                    dict(a=2, b=[dict(a=1), dict(a=2)]),
                    dict(a=3, b=[dict(a="a")]),
                ]
            )
            == "[x.1.2<[x.1.2][1.2.x]>][1.2.3<[x.1.2][1.2.x]>][2.3.x<[x.a.x]>]"
        )

    def test_recursive_depth0(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for item in seq recursive %}[{{ loop.depth0 }}:{{ item.a }}"
            "{% if item.b %}<{{ loop(item.b) }}>{% endif %}]{% endfor %}"
        )
        assert (
            tmpl.render(
                seq=[
                    dict(a=1, b=[dict(a=1), dict(a=2)]),
                    dict(a=2, b=[dict(a=1), dict(a=2)]),
                    dict(a=3, b=[dict(a="a")]),
                ]
            )
            == "[0:1<[1:1][1:2]>][0:2<[1:1][1:2]>][0:3<[1:a]>]"
        )

    def test_recursive_depth(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for item in seq recursive %}[{{ loop.depth }}:{{ item.a }}"
            "{% if item.b %}<{{ loop(item.b) }}>{% endif %}]{% endfor %}"
        )
        assert (
            tmpl.render(
                seq=[
                    dict(a=1, b=[dict(a=1), dict(a=2)]),
                    dict(a=2, b=[dict(a=1), dict(a=2)]),
                    dict(a=3, b=[dict(a="a")]),
                ]
            )
            == "[1:1<[2:1][2:2]>][1:2<[2:1][2:2]>][1:3<[2:a]>]"
        )

    def test_looploop(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for row in table %}
            {%- set rowloop = loop -%}
            {% for cell in row -%}
                [{{ rowloop.index }}|{{ loop.index }}]
            {%- endfor %}
        {%- endfor %}"""
        )
        assert tmpl.render(table=["ab", "cd"]) == "[1|1][1|2][2|1][2|2]"

    def test_reversed_bug(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for i in items %}{{ i }}"
            "{% if not loop.last %}"
            ",{% endif %}{% endfor %}"
        )
        assert tmpl.render(items=reversed([3, 2, 1])) == "1,2,3"

    def test_loop_errors(self, test_env_async):
        tmpl = test_env_async.from_string(
            """{% for item in [1] if loop.index
                                      == 0 %}...{% endfor %}"""
        )
        pytest.raises(UndefinedError, tmpl.render)
        tmpl = test_env_async.from_string(
            """{% for item in [] %}...{% else
            %}{{ loop }}{% endfor %}"""
        )
        assert tmpl.render() == ""

    def test_loop_filter(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for item in range(10) if item is even %}[{{ item }}]{% endfor %}"
        )
        assert tmpl.render() == "[0][2][4][6][8]"
        tmpl = test_env_async.from_string(
            """
            {%- for item in range(10) if item is even %}[{{
                loop.index }}:{{ item }}]{% endfor %}"""
        )
        assert tmpl.render() == "[1:0][2:2][3:4][4:6][5:8]"

    def test_scoped_special_var(self, test_env_async):
        t = test_env_async.from_string(
            "{% for s in seq %}[{{ loop.first }}{% for c in s %}"
            "|{{ loop.first }}{% endfor %}]{% endfor %}"
        )
        assert t.render(seq=("ab", "cd")) == "[True|True|False][False|True|False]"

    def test_scoped_loop_var(self, test_env_async):
        t = test_env_async.from_string(
            "{% for x in seq %}{{ loop.first }}"
            "{% for y in seq %}{% endfor %}{% endfor %}"
        )
        assert t.render(seq="ab") == "TrueFalse"
        t = test_env_async.from_string(
            "{% for x in seq %}{% for y in seq %}"
            "{{ loop.first }}{% endfor %}{% endfor %}"
        )
        assert t.render(seq="ab") == "TrueFalseTrueFalse"

    def test_recursive_empty_loop_iter(self, test_env_async):
        t = test_env_async.from_string(
            """
        {%- for item in foo recursive -%}{%- endfor -%}
        """
        )
        assert t.render(dict(foo=[])) == ""

    def test_call_in_loop(self, test_env_async):
        t = test_env_async.from_string(
            """
        {%- macro do_something() -%}
            [{{ caller() }}]
        {%- endmacro %}

        {%- for i in [1, 2, 3] %}
            {%- call do_something() -%}
                {{ i }}
            {%- endcall %}
        {%- endfor -%}
        """
        )
        assert t.render() == "[1][2][3]"

    def test_scoping_bug(self, test_env_async):
        t = test_env_async.from_string(
            """
        {%- for item in foo %}...{{ item }}...{% endfor %}
        {%- macro item(a) %}...{{ a }}...{% endmacro %}
        {{- item(2) -}}
        """
        )
        assert t.render(foo=(1,)) == "...1......2..."

    def test_unpacking(self, test_env_async):
        tmpl = test_env_async.from_string(
            "{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}"
        )
        assert tmpl.render() == "1|2|3"

    def test_recursive_loop_filter(self, test_env_async):
        t = test_env_async.from_string(
            """
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          {%- for page in [site.root] if page.url != this recursive %}
          <url><loc>{{ page.url }}</loc></url>
          {{- loop(page.children) }}
          {%- endfor %}
        </urlset>
        """
        )
        sm = t.render(
            this="/foo",
            site={"root": {"url": "/", "children": [{"url": "/foo"}, {"url": "/bar"}]}},
        )
        lines = [x.strip() for x in sm.splitlines() if x.strip()]
        assert lines == [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            "<url><loc>/</loc></url>",
            "<url><loc>/bar</loc></url>",
            "</urlset>",
        ]

    def test_nonrecursive_loop_filter(self, test_env_async):
        t = test_env_async.from_string(
            """
        <?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          {%- for page in items if page.url != this %}
          <url><loc>{{ page.url }}</loc></url>
          {%- endfor %}
        </urlset>
        """
        )
        sm = t.render(
            this="/foo", items=[{"url": "/"}, {"url": "/foo"}, {"url": "/bar"}]
        )
        lines = [x.strip() for x in sm.splitlines() if x.strip()]
        assert lines == [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            "<url><loc>/</loc></url>",
            "<url><loc>/bar</loc></url>",
            "</urlset>",
        ]

    def test_bare_async(self, test_env_async):
        t = test_env_async.from_string('{% extends "header" %}')
        assert t.render(foo=42) == "[42|23]"

    def test_awaitable_property_slicing(self, test_env_async):
        t = test_env_async.from_string("{% for x in a.b[:1] %}{{ x }}{% endfor %}")
        assert t.render(a=dict(b=[1, 2, 3])) == "1"


def test_namespace_awaitable(test_env_async):
    async def _test():
        t = test_env_async.from_string(
            '{% set ns = namespace(foo="Bar") %}{{ ns.foo }}'
        )
        actual = await t.render_async()
        assert actual == "Bar"

    run(_test())
