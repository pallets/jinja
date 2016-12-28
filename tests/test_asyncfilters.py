import pytest
from jinja2 import Environment


async def make_aiter(iter):
    for item in iter:
        yield item


@pytest.fixture
def env_async():
    return Environment(enable_async=True)


@pytest.mark.parametrize('foo', [
    lambda: range(10),
    lambda: make_aiter(range(10)),
])
def test_first(env_async, foo):
    tmpl = env_async.from_string('{{ foo()|first }}')
    out = tmpl.render(foo=foo)
    assert out == '0'


def test_groupby(env_async):
    tmpl = env_async.from_string('''
    {%- for grouper, list in [{'foo': 1, 'bar': 2},
                              {'foo': 2, 'bar': 3},
                              {'foo': 1, 'bar': 1},
                              {'foo': 3, 'bar': 4}]|groupby('foo') -%}
        {{ grouper }}{% for x in list %}: {{ x.foo }}, {{ x.bar }}{% endfor %}|
    {%- endfor %}''')
    assert tmpl.render().split('|') == [
        "1: 1, 2: 1, 1",
        "2: 2, 3",
        "3: 3, 4",
        ""
    ]


def test_groupby_tuple_index(env_async):
    tmpl = env_async.from_string('''
    {%- for grouper, list in [('a', 1), ('a', 2), ('b', 1)]|groupby(0) -%}
        {{ grouper }}{% for x in list %}:{{ x.1 }}{% endfor %}|
    {%- endfor %}''')
    assert tmpl.render() == 'a:1:2|b:1|'


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


@pytest.mark.parametrize('articles', [
    make_articles,
    lambda: make_aiter(make_articles()),
])
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
