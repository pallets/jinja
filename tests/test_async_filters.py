import asyncio
import contextlib
from collections import namedtuple

import pytest
import trio
from markupsafe import Markup

from jinja2 import Environment
from jinja2.async_utils import auto_aiter


async def make_aiter(iter):
    for item in iter:
        yield item


def mark_dualiter(parameter, factory):
    def decorator(f):
        return pytest.mark.parametrize(
            parameter, [lambda: factory(), lambda: make_aiter(factory())]
        )(f)

    return decorator


@pytest.fixture
def env_async():
    return Environment(enable_async=True)


def _asyncio_run(async_fn, *args):
    return asyncio.run(async_fn(*args))


@pytest.fixture(params=[_asyncio_run, trio.run], ids=["asyncio", "trio"])
def run_async_fn(request):
    return request.param


@contextlib.asynccontextmanager
async def closing_factory():
    async with contextlib.AsyncExitStack() as stack:

        def closing(maybe_agen):
            try:
                aclose = maybe_agen.aclose
            except AttributeError:
                pass
            else:
                stack.push_async_callback(aclose)
            return maybe_agen

        yield closing


@mark_dualiter("foo", lambda: range(10))
def test_first(env_async, foo, run_async_fn):
    async def test():
        async with closing_factory() as closing:
            tmpl = env_async.from_string("{{ closing(foo())|first }}")
            return await tmpl.render_async(foo=foo, closing=closing)

    out = run_async_fn(test)
    assert out == "0"


@mark_dualiter(
    "items",
    lambda: [
        {"foo": 1, "bar": 2},
        {"foo": 2, "bar": 3},
        {"foo": 1, "bar": 1},
        {"foo": 3, "bar": 4},
    ],
)
def test_groupby(env_async, items):
    tmpl = env_async.from_string(
        """
    {%- for grouper, list in items()|groupby('foo') -%}
        {{ grouper }}{% for x in list %}: {{ x.foo }}, {{ x.bar }}{% endfor %}|
    {%- endfor %}"""
    )
    assert tmpl.render(items=items).split("|") == [
        "1: 1, 2: 1, 1",
        "2: 2, 3",
        "3: 3, 4",
        "",
    ]


@pytest.mark.parametrize(
    ("case_sensitive", "expect"),
    [
        (False, "a: 1, 3\nb: 2\n"),
        (True, "A: 3\na: 1\nb: 2\n"),
    ],
)
def test_groupby_case(env_async, case_sensitive, expect):
    tmpl = env_async.from_string(
        "{% for k, vs in data|groupby('k', case_sensitive=cs) %}"
        "{{ k }}: {{ vs|join(', ', attribute='v') }}\n"
        "{% endfor %}"
    )
    out = tmpl.render(
        data=[{"k": "a", "v": 1}, {"k": "b", "v": 2}, {"k": "A", "v": 3}],
        cs=case_sensitive,
    )
    assert out == expect


@mark_dualiter("items", lambda: [("a", 1), ("a", 2), ("b", 1)])
def test_groupby_tuple_index(env_async, items):
    tmpl = env_async.from_string(
        """
    {%- for grouper, list in items()|groupby(0) -%}
        {{ grouper }}{% for x in list %}:{{ x.1 }}{% endfor %}|
    {%- endfor %}"""
    )
    assert tmpl.render(items=items) == "a:1:2|b:1|"


def make_articles():
    Date = namedtuple("Date", "day,month,year")
    Article = namedtuple("Article", "title,date")
    return [
        Article("aha", Date(1, 1, 1970)),
        Article("interesting", Date(2, 1, 1970)),
        Article("really?", Date(3, 1, 1970)),
        Article("totally not", Date(1, 1, 1971)),
    ]


@mark_dualiter("articles", make_articles)
def test_groupby_multidot(env_async, articles):
    tmpl = env_async.from_string(
        """
    {%- for year, list in articles()|groupby('date.year') -%}
        {{ year }}{% for x in list %}[{{ x.title }}]{% endfor %}|
    {%- endfor %}"""
    )
    assert tmpl.render(articles=articles).split("|") == [
        "1970[aha][interesting][really?]",
        "1971[totally not]",
        "",
    ]


@mark_dualiter("int_items", lambda: [1, 2, 3])
def test_join_env_int(env_async, int_items):
    tmpl = env_async.from_string('{{ items()|join("|") }}')
    out = tmpl.render(items=int_items)
    assert out == "1|2|3"


@mark_dualiter("string_items", lambda: ["<foo>", Markup("<span>foo</span>")])
def test_join_string_list(string_items):
    env2 = Environment(autoescape=True, enable_async=True)
    tmpl = env2.from_string('{{ ["<foo>", "<span>foo</span>"|safe]|join }}')
    assert tmpl.render(items=string_items) == "&lt;foo&gt;<span>foo</span>"


def make_users():
    User = namedtuple("User", "username")
    return map(User, ["foo", "bar"])


@mark_dualiter("users", make_users)
def test_join_attribute(env_async, users):
    tmpl = env_async.from_string("""{{ users()|join(', ', 'username') }}""")
    assert tmpl.render(users=users) == "foo, bar"


@mark_dualiter("items", lambda: [1, 2, 3, 4, 5])
def test_simple_reject(env_async, items):
    tmpl = env_async.from_string('{{ items()|reject("odd")|join("|") }}')
    assert tmpl.render(items=items) == "2|4"


@mark_dualiter("items", lambda: [None, False, 0, 1, 2, 3, 4, 5])
def test_bool_reject(env_async, items):
    tmpl = env_async.from_string('{{ items()|reject|join("|") }}')
    assert tmpl.render(items=items) == "None|False|0"


@mark_dualiter("items", lambda: [1, 2, 3, 4, 5])
def test_simple_select(env_async, items):
    tmpl = env_async.from_string('{{ items()|select("odd")|join("|") }}')
    assert tmpl.render(items=items) == "1|3|5"


@mark_dualiter("items", lambda: [None, False, 0, 1, 2, 3, 4, 5])
def test_bool_select(env_async, items):
    tmpl = env_async.from_string('{{ items()|select|join("|") }}')
    assert tmpl.render(items=items) == "1|2|3|4|5"


def make_users():  # type: ignore
    User = namedtuple("User", "name,is_active")
    return [
        User("john", True),
        User("jane", True),
        User("mike", False),
    ]


@mark_dualiter("users", make_users)
def test_simple_select_attr(env_async, users):
    tmpl = env_async.from_string(
        '{{ users()|selectattr("is_active")|map(attribute="name")|join("|") }}'
    )
    assert tmpl.render(users=users) == "john|jane"


@mark_dualiter("items", lambda: list("123"))
def test_simple_map(env_async, items):
    tmpl = env_async.from_string('{{ items()|map("int")|sum }}')
    assert tmpl.render(items=items) == "6"


@mark_dualiter("items", lambda: list("1423"))
def test_simple_map_sort(env_async, items):
    tmpl = env_async.from_string('{{ items()|map("int")|sort }}')
    assert tmpl.render(items=items) == "[1, 2, 3, 4]"


def test_map_sum(env_async):  # async map + async filter
    tmpl = env_async.from_string('{{ [[1,2], [3], [4,5,6]]|map("sum")|list }}')
    assert tmpl.render() == "[3, 3, 15]"


@mark_dualiter("users", make_users)
def test_attribute_map(env_async, users):
    tmpl = env_async.from_string('{{ users()|map(attribute="name")|join("|") }}')
    assert tmpl.render(users=users) == "john|jane|mike"


def test_empty_map(env_async):
    tmpl = env_async.from_string('{{ none|map("upper")|list }}')
    assert tmpl.render() == "[]"


@mark_dualiter("items", lambda: [1, 2, 3, 4, 5, 6])
def test_sum(env_async, items):
    tmpl = env_async.from_string("""{{ items()|sum }}""")
    assert tmpl.render(items=items) == "21"


@mark_dualiter("items", lambda: [{"value": 23}, {"value": 1}, {"value": 18}])
def test_sum_attributes(env_async, items):
    tmpl = env_async.from_string("""{{ items()|sum('value') }}""")
    assert tmpl.render(items=items)


def test_sum_attributes_nested(env_async):
    tmpl = env_async.from_string("""{{ values|sum('real.value') }}""")
    assert (
        tmpl.render(
            values=[
                {"real": {"value": 23}},
                {"real": {"value": 1}},
                {"real": {"value": 18}},
            ]
        )
        == "42"
    )


def test_sum_attributes_tuple(env_async):
    tmpl = env_async.from_string("""{{ values.items()|sum('1') }}""")
    assert tmpl.render(values={"foo": 23, "bar": 1, "baz": 18}) == "42"


@mark_dualiter("items", lambda: range(10))
def test_slice(env_async, items):
    tmpl = env_async.from_string(
        "{{ items()|slice(3)|list }}|{{ items()|slice(3, 'X')|list }}"
    )
    out = tmpl.render(items=items)
    assert out == (
        "[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]|"
        "[[0, 1, 2, 3], [4, 5, 6, 'X'], [7, 8, 9, 'X']]"
    )


def test_unique_with_async_gen(env_async):
    items = ["a", "b", "c", "c", "a", "d", "z"]
    tmpl = env_async.from_string("{{ items|reject('==', 'z')|unique|list }}")
    out = tmpl.render(items=items)
    assert out == "['a', 'b', 'c', 'd']"


def test_custom_async_filter(env_async, run_async_fn):
    async def customfilter(val):
        return str(val)

    async def test():
        env_async.filters["customfilter"] = customfilter
        tmpl = env_async.from_string(
            "{{ 'static'|customfilter }} {{ arg|customfilter }}"
        )
        return await tmpl.render_async(arg="dynamic")

    out = run_async_fn(test)
    assert out == "static dynamic"


@mark_dualiter("items", lambda: range(10))
def test_custom_async_iteratable_filter(env_async, items, run_async_fn):
    async def customfilter(iterable):
        items = []
        async for item in auto_aiter(iterable):
            items.append(str(item))
            if len(items) == 3:
                break
        return ",".join(items)

    async def test():
        async with closing_factory() as closing:
            env_async.filters["customfilter"] = customfilter
            tmpl = env_async.from_string(
                "{{ closing(items())|customfilter }} .. {{ [3, 4, 5, 6]|customfilter }}"
            )
            return await tmpl.render_async(items=items, closing=closing)

    out = run_async_fn(test)
    assert out == "0,1,2 .. 3,4,5"
