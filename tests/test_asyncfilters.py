import pytest
from jinja2 import Environment


async def make_aiter(iter):
    for item in iter:
        yield item


def mark_dualiter(parameter, factory):
    def decorator(f):
        return pytest.mark.parametrize(parameter, [
            lambda: factory(),
            lambda: make_aiter(factory()),
        ])(f)
    return decorator


@pytest.fixture
def env_async():
    return Environment(enable_async=True)


@mark_dualiter('foo', lambda: range(10))
def test_first(env_async, foo):
    tmpl = env_async.from_string('{{ foo()|first }}')
    out = tmpl.render(foo=foo)
    assert out == '0'


@mark_dualiter('items', lambda: [
    {'foo': 1, 'bar': 2},
    {'foo': 2, 'bar': 3},
    {'foo': 1, 'bar': 1},
    {'foo': 3, 'bar': 4}
])
def test_groupby(env_async, items):
    tmpl = env_async.from_string('''
    {%- for grouper, list in items()|groupby('foo') -%}
        {{ grouper }}{% for x in list %}: {{ x.foo }}, {{ x.bar }}{% endfor %}|
    {%- endfor %}''')
    assert tmpl.render(items=items).split('|') == [
        "1: 1, 2: 1, 1",
        "2: 2, 3",
        "3: 3, 4",
        ""
    ]


@mark_dualiter('items', lambda: [('a', 1), ('a', 2), ('b', 1)])
def test_groupby_tuple_index(env_async, items):
    tmpl = env_async.from_string('''
    {%- for grouper, list in items()|groupby(0) -%}
        {{ grouper }}{% for x in list %}:{{ x.1 }}{% endfor %}|
    {%- endfor %}''')
    assert tmpl.render(items=items) == 'a:1:2|b:1|'


def make_articles():
    class Date(object):
        def __init__(self, day, month, year):
            self.day = day
            self.month = month
            self.year = year

    class Article(object):
        def __init__(self, title, *date):
            self.date = Date(*date)
            self.title = title

    return [
        Article('aha', 1, 1, 1970),
        Article('interesting', 2, 1, 1970),
        Article('really?', 3, 1, 1970),
        Article('totally not', 1, 1, 1971)
    ]


@mark_dualiter('articles', make_articles)
def test_groupby_multidot(env_async, articles):
    tmpl = env_async.from_string('''
    {%- for year, list in articles()|groupby('date.year') -%}
        {{ year }}{% for x in list %}[{{ x.title }}]{% endfor %}|
    {%- endfor %}''')
    assert tmpl.render(articles=articles).split('|') == [
        '1970[aha][interesting][really?]',
        '1971[totally not]',
        ''
    ]
