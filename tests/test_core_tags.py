import pytest

from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import TemplateRuntimeError
from jinja2 import TemplateSyntaxError
from jinja2 import UndefinedError


@pytest.fixture
def env_trim():
    return Environment(trim_blocks=True)


class TestForLoop:
    def test_simple(self, env):
        tmpl = env.from_string("{% for item in seq %}{{ item }}{% endfor %}")
        assert tmpl.render(seq=list(range(10))) == "0123456789"

    def test_else(self, env):
        tmpl = env.from_string("{% for item in seq %}XXX{% else %}...{% endfor %}")
        assert tmpl.render() == "..."

    def test_else_scoping_item(self, env):
        tmpl = env.from_string("{% for item in [] %}{% else %}{{ item }}{% endfor %}")
        assert tmpl.render(item=42) == "42"

    def test_empty_blocks(self, env):
        tmpl = env.from_string("<{% for item in seq %}{% else %}{% endfor %}>")
        assert tmpl.render() == "<>"

    def test_context_vars(self, env):
        slist = [42, 24]
        for seq in [slist, iter(slist), reversed(slist), (_ for _ in slist)]:
            tmpl = env.from_string(
                """{% for item in seq -%}
            {{ loop.index }}|{{ loop.index0 }}|{{ loop.revindex }}|{{
                loop.revindex0 }}|{{ loop.first }}|{{ loop.last }}|{{
               loop.length }}###{% endfor %}"""
            )
            one, two, _ = tmpl.render(seq=seq).split("###")
            (
                one_index,
                one_index0,
                one_revindex,
                one_revindex0,
                one_first,
                one_last,
                one_length,
            ) = one.split("|")
            (
                two_index,
                two_index0,
                two_revindex,
                two_revindex0,
                two_first,
                two_last,
                two_length,
            ) = two.split("|")

            assert int(one_index) == 1 and int(two_index) == 2
            assert int(one_index0) == 0 and int(two_index0) == 1
            assert int(one_revindex) == 2 and int(two_revindex) == 1
            assert int(one_revindex0) == 1 and int(two_revindex0) == 0
            assert one_first == "True" and two_first == "False"
            assert one_last == "False" and two_last == "True"
            assert one_length == two_length == "2"

    def test_cycling(self, env):
        tmpl = env.from_string(
            """{% for item in seq %}{{
            loop.cycle('<1>', '<2>') }}{% endfor %}{%
            for item in seq %}{{ loop.cycle(*through) }}{% endfor %}"""
        )
        output = tmpl.render(seq=list(range(4)), through=("<1>", "<2>"))
        assert output == "<1><2>" * 4

    def test_lookaround(self, env):
        tmpl = env.from_string(
            """{% for item in seq -%}
            {{ loop.previtem|default('x') }}-{{ item }}-{{
            loop.nextitem|default('x') }}|
        {%- endfor %}"""
        )
        output = tmpl.render(seq=list(range(4)))
        assert output == "x-0-1|0-1-2|1-2-3|2-3-x|"

    def test_changed(self, env):
        tmpl = env.from_string(
            """{% for item in seq -%}
            {{ loop.changed(item) }},
        {%- endfor %}"""
        )
        output = tmpl.render(seq=[None, None, 1, 2, 2, 3, 4, 4, 4])
        assert output == "True,False,True,True,False,True,True,False,False,"

    def test_scope(self, env):
        tmpl = env.from_string("{% for item in seq %}{% endfor %}{{ item }}")
        output = tmpl.render(seq=list(range(10)))
        assert not output

    def test_varlen(self, env):
        tmpl = env.from_string("{% for item in iter %}{{ item }}{% endfor %}")
        output = tmpl.render(iter=range(5))
        assert output == "01234"

    def test_noniter(self, env):
        tmpl = env.from_string("{% for item in none %}...{% endfor %}")
        pytest.raises(TypeError, tmpl.render)

    def test_recursive(self, env):
        tmpl = env.from_string(
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

    def test_recursive_lookaround(self, env):
        tmpl = env.from_string(
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

    def test_recursive_depth0(self, env):
        tmpl = env.from_string(
            """{% for item in seq recursive -%}
        [{{ loop.depth0 }}:{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
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
            == "[0:1<[1:1][1:2]>][0:2<[1:1][1:2]>][0:3<[1:a]>]"
        )

    def test_recursive_depth(self, env):
        tmpl = env.from_string(
            """{% for item in seq recursive -%}
        [{{ loop.depth }}:{{ item.a }}{% if item.b %}<{{ loop(item.b) }}>{% endif %}]
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
            == "[1:1<[2:1][2:2]>][1:2<[2:1][2:2]>][1:3<[2:a]>]"
        )

    def test_looploop(self, env):
        tmpl = env.from_string(
            """{% for row in table %}
            {%- set rowloop = loop -%}
            {% for cell in row -%}
                [{{ rowloop.index }}|{{ loop.index }}]
            {%- endfor %}
        {%- endfor %}"""
        )
        assert tmpl.render(table=["ab", "cd"]) == "[1|1][1|2][2|1][2|2]"

    def test_reversed_bug(self, env):
        tmpl = env.from_string(
            "{% for i in items %}{{ i }}"
            "{% if not loop.last %}"
            ",{% endif %}{% endfor %}"
        )
        assert tmpl.render(items=reversed([3, 2, 1])) == "1,2,3"

    def test_loop_errors(self, env):
        tmpl = env.from_string(
            """{% for item in [1] if loop.index
                                      == 0 %}...{% endfor %}"""
        )
        pytest.raises(UndefinedError, tmpl.render)
        tmpl = env.from_string(
            """{% for item in [] %}...{% else
            %}{{ loop }}{% endfor %}"""
        )
        assert tmpl.render() == ""

    def test_loop_filter(self, env):
        tmpl = env.from_string(
            "{% for item in range(10) if item is even %}[{{ item }}]{% endfor %}"
        )
        assert tmpl.render() == "[0][2][4][6][8]"
        tmpl = env.from_string(
            """
            {%- for item in range(10) if item is even %}[{{
                loop.index }}:{{ item }}]{% endfor %}"""
        )
        assert tmpl.render() == "[1:0][2:2][3:4][4:6][5:8]"

    def test_loop_unassignable(self, env):
        pytest.raises(
            TemplateSyntaxError, env.from_string, "{% for loop in seq %}...{% endfor %}"
        )

    def test_scoped_special_var(self, env):
        t = env.from_string(
            "{% for s in seq %}[{{ loop.first }}{% for c in s %}"
            "|{{ loop.first }}{% endfor %}]{% endfor %}"
        )
        assert t.render(seq=("ab", "cd")) == "[True|True|False][False|True|False]"

    def test_scoped_loop_var(self, env):
        t = env.from_string(
            "{% for x in seq %}{{ loop.first }}"
            "{% for y in seq %}{% endfor %}{% endfor %}"
        )
        assert t.render(seq="ab") == "TrueFalse"
        t = env.from_string(
            "{% for x in seq %}{% for y in seq %}"
            "{{ loop.first }}{% endfor %}{% endfor %}"
        )
        assert t.render(seq="ab") == "TrueFalseTrueFalse"

    def test_recursive_empty_loop_iter(self, env):
        t = env.from_string(
            """
        {%- for item in foo recursive -%}{%- endfor -%}
        """
        )
        assert t.render(dict(foo=[])) == ""

    def test_call_in_loop(self, env):
        t = env.from_string(
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

    def test_scoping_bug(self, env):
        t = env.from_string(
            """
        {%- for item in foo %}...{{ item }}...{% endfor %}
        {%- macro item(a) %}...{{ a }}...{% endmacro %}
        {{- item(2) -}}
        """
        )
        assert t.render(foo=(1,)) == "...1......2..."

    def test_unpacking(self, env):
        tmpl = env.from_string(
            "{% for a, b, c in [[1, 2, 3]] %}{{ a }}|{{ b }}|{{ c }}{% endfor %}"
        )
        assert tmpl.render() == "1|2|3"

    def test_intended_scoping_with_set(self, env):
        tmpl = env.from_string(
            "{% for item in seq %}{{ x }}{% set x = item %}{{ x }}{% endfor %}"
        )
        assert tmpl.render(x=0, seq=[1, 2, 3]) == "010203"

        tmpl = env.from_string(
            "{% set x = 9 %}{% for item in seq %}{{ x }}"
            "{% set x = item %}{{ x }}{% endfor %}"
        )
        assert tmpl.render(x=0, seq=[1, 2, 3]) == "919293"


class TestIfCondition:
    def test_simple(self, env):
        tmpl = env.from_string("""{% if true %}...{% endif %}""")
        assert tmpl.render() == "..."

    def test_elif(self, env):
        tmpl = env.from_string(
            """{% if false %}XXX{% elif true
            %}...{% else %}XXX{% endif %}"""
        )
        assert tmpl.render() == "..."

    def test_elif_deep(self, env):
        elifs = "\n".join(f"{{% elif a == {i} %}}{i}" for i in range(1, 1000))
        tmpl = env.from_string(f"{{% if a == 0 %}}0{elifs}{{% else %}}x{{% endif %}}")
        for x in (0, 10, 999):
            assert tmpl.render(a=x).strip() == str(x)
        assert tmpl.render(a=1000).strip() == "x"

    def test_else(self, env):
        tmpl = env.from_string("{% if false %}XXX{% else %}...{% endif %}")
        assert tmpl.render() == "..."

    def test_empty(self, env):
        tmpl = env.from_string("[{% if true %}{% else %}{% endif %}]")
        assert tmpl.render() == "[]"

    def test_complete(self, env):
        tmpl = env.from_string(
            "{% if a %}A{% elif b %}B{% elif c == d %}C{% else %}D{% endif %}"
        )
        assert tmpl.render(a=0, b=False, c=42, d=42.0) == "C"

    def test_no_scope(self, env):
        tmpl = env.from_string("{% if a %}{% set foo = 1 %}{% endif %}{{ foo }}")
        assert tmpl.render(a=True) == "1"
        tmpl = env.from_string("{% if true %}{% set foo = 1 %}{% endif %}{{ foo }}")
        assert tmpl.render() == "1"


class TestMacros:
    def test_simple(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro say_hello(name) %}Hello {{ name }}!{% endmacro %}
{{ say_hello('Peter') }}"""
        )
        assert tmpl.render() == "Hello Peter!"

    def test_scoping(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro level1(data1) %}
{% macro level2(data2) %}{{ data1 }}|{{ data2 }}{% endmacro %}
{{ level2('bar') }}{% endmacro %}
{{ level1('foo') }}"""
        )
        assert tmpl.render() == "foo|bar"

    def test_arguments(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro m(a, b, c='c', d='d') %}{{ a }}|{{ b }}|{{ c }}|{{ d }}{% endmacro %}
{{ m() }}|{{ m('a') }}|{{ m('a', 'b') }}|{{ m(1, 2, 3) }}"""
        )
        assert tmpl.render() == "||c|d|a||c|d|a|b|c|d|1|2|3|d"

    def test_arguments_defaults_nonsense(self, env_trim):
        pytest.raises(
            TemplateSyntaxError,
            env_trim.from_string,
            """\
{% macro m(a, b=1, c) %}a={{ a }}, b={{ b }}, c={{ c }}{% endmacro %}""",
        )

    def test_caller_defaults_nonsense(self, env_trim):
        pytest.raises(
            TemplateSyntaxError,
            env_trim.from_string,
            """\
{% macro a() %}{{ caller() }}{% endmacro %}
{% call(x, y=1, z) a() %}{% endcall %}""",
        )

    def test_varargs(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro test() %}{{ varargs|join('|') }}{% endmacro %}\
{{ test(1, 2, 3) }}"""
        )
        assert tmpl.render() == "1|2|3"

    def test_simple_call(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro test() %}[[{{ caller() }}]]{% endmacro %}\
{% call test() %}data{% endcall %}"""
        )
        assert tmpl.render() == "[[data]]"

    def test_complex_call(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% macro test() %}[[{{ caller('data') }}]]{% endmacro %}\
{% call(data) test() %}{{ data }}{% endcall %}"""
        )
        assert tmpl.render() == "[[data]]"

    def test_caller_undefined(self, env_trim):
        tmpl = env_trim.from_string(
            """\
{% set caller = 42 %}\
{% macro test() %}{{ caller is not defined }}{% endmacro %}\
{{ test() }}"""
        )
        assert tmpl.render() == "True"

    def test_include(self, env_trim):
        env_trim = Environment(
            loader=DictLoader(
                {"include": "{% macro test(foo) %}[{{ foo }}]{% endmacro %}"}
            )
        )
        tmpl = env_trim.from_string('{% from "include" import test %}{{ test("foo") }}')
        assert tmpl.render() == "[foo]"

    def test_macro_api(self, env_trim):
        tmpl = env_trim.from_string(
            "{% macro foo(a, b) %}{% endmacro %}"
            "{% macro bar() %}{{ varargs }}{{ kwargs }}{% endmacro %}"
            "{% macro baz() %}{{ caller() }}{% endmacro %}"
        )
        assert tmpl.module.foo.arguments == ("a", "b")
        assert tmpl.module.foo.name == "foo"
        assert not tmpl.module.foo.caller
        assert not tmpl.module.foo.catch_kwargs
        assert not tmpl.module.foo.catch_varargs
        assert tmpl.module.bar.arguments == ()
        assert not tmpl.module.bar.caller
        assert tmpl.module.bar.catch_kwargs
        assert tmpl.module.bar.catch_varargs
        assert tmpl.module.baz.caller

    def test_callself(self, env_trim):
        tmpl = env_trim.from_string(
            "{% macro foo(x) %}{{ x }}{% if x > 1 %}|"
            "{{ foo(x - 1) }}{% endif %}{% endmacro %}"
            "{{ foo(5) }}"
        )
        assert tmpl.render() == "5|4|3|2|1"

    def test_macro_defaults_self_ref(self, env):
        tmpl = env.from_string(
            """
            {%- set x = 42 %}
            {%- macro m(a, b=x, x=23) %}{{ a }}|{{ b }}|{{ x }}{% endmacro -%}
        """
        )
        assert tmpl.module.m(1) == "1||23"
        assert tmpl.module.m(1, 2) == "1|2|23"
        assert tmpl.module.m(1, 2, 3) == "1|2|3"
        assert tmpl.module.m(1, x=7) == "1|7|7"


class TestSet:
    def test_normal(self, env_trim):
        tmpl = env_trim.from_string("{% set foo = 1 %}{{ foo }}")
        assert tmpl.render() == "1"
        assert tmpl.module.foo == 1

    def test_block(self, env_trim):
        tmpl = env_trim.from_string("{% set foo %}42{% endset %}{{ foo }}")
        assert tmpl.render() == "42"
        assert tmpl.module.foo == "42"

    def test_block_escaping(self):
        env = Environment(autoescape=True)
        tmpl = env.from_string(
            "{% set foo %}<em>{{ test }}</em>{% endset %}foo: {{ foo }}"
        )
        assert tmpl.render(test="<unsafe>") == "foo: <em>&lt;unsafe&gt;</em>"

    def test_set_invalid(self, env_trim):
        pytest.raises(
            TemplateSyntaxError, env_trim.from_string, "{% set foo['bar'] = 1 %}"
        )
        tmpl = env_trim.from_string("{% set foo.bar = 1 %}")
        exc_info = pytest.raises(TemplateRuntimeError, tmpl.render, foo={})
        assert "non-namespace object" in exc_info.value.message

    def test_namespace_redefined(self, env_trim):
        tmpl = env_trim.from_string("{% set ns = namespace() %}{% set ns.bar = 'hi' %}")
        exc_info = pytest.raises(TemplateRuntimeError, tmpl.render, namespace=dict)
        assert "non-namespace object" in exc_info.value.message

    def test_namespace(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set ns = namespace() %}{% set ns.bar = '42' %}{{ ns.bar }}"
        )
        assert tmpl.render() == "42"

    def test_namespace_block(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set ns = namespace() %}{% set ns.bar %}42{% endset %}{{ ns.bar }}"
        )
        assert tmpl.render() == "42"

    def test_init_namespace(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set ns = namespace(d, self=37) %}"
            "{% set ns.b = 42 %}"
            "{{ ns.a }}|{{ ns.self }}|{{ ns.b }}"
        )
        assert tmpl.render(d={"a": 13}) == "13|37|42"

    def test_namespace_loop(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set ns = namespace(found=false) %}"
            "{% for x in range(4) %}"
            "{% if x == v %}"
            "{% set ns.found = true %}"
            "{% endif %}"
            "{% endfor %}"
            "{{ ns.found }}"
        )
        assert tmpl.render(v=3) == "True"
        assert tmpl.render(v=4) == "False"

    def test_namespace_macro(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set ns = namespace() %}"
            "{% set ns.a = 13 %}"
            "{% macro magic(x) %}"
            "{% set x.b = 37 %}"
            "{% endmacro %}"
            "{{ magic(ns) }}"
            "{{ ns.a }}|{{ ns.b }}"
        )
        assert tmpl.render() == "13|37"

    def test_block_escaping_filtered(self):
        env = Environment(autoescape=True)
        tmpl = env.from_string(
            "{% set foo | trim %}<em>{{ test }}</em>    {% endset %}foo: {{ foo }}"
        )
        assert tmpl.render(test="<unsafe>") == "foo: <em>&lt;unsafe&gt;</em>"

    def test_block_filtered(self, env_trim):
        tmpl = env_trim.from_string(
            "{% set foo | trim | length | string %} 42    {% endset %}{{ foo }}"
        )
        assert tmpl.render() == "2"
        assert tmpl.module.foo == "2"

    def test_block_filtered_set(self, env_trim):
        def _myfilter(val, arg):
            assert arg == " xxx "
            return val

        env_trim.filters["myfilter"] = _myfilter
        tmpl = env_trim.from_string(
            '{% set a = " xxx " %}'
            "{% set foo | myfilter(a) | trim | length | string %}"
            ' {% set b = " yy " %} 42 {{ a }}{{ b }}   '
            "{% endset %}"
            "{{ foo }}"
        )
        assert tmpl.render() == "11"
        assert tmpl.module.foo == "11"


class TestWith:
    def test_with(self, env):
        tmpl = env.from_string(
            """\
        {% with a=42, b=23 -%}
            {{ a }} = {{ b }}
        {% endwith -%}
            {{ a }} = {{ b }}\
        """
        )
        assert [x.strip() for x in tmpl.render(a=1, b=2).splitlines()] == [
            "42 = 23",
            "1 = 2",
        ]

    def test_with_argument_scoping(self, env):
        tmpl = env.from_string(
            """\
        {%- with a=1, b=2, c=b, d=e, e=5 -%}
            {{ a }}|{{ b }}|{{ c }}|{{ d }}|{{ e }}
        {%- endwith -%}
        """
        )
        assert tmpl.render(b=3, e=4) == "1|2|3|4|5"
