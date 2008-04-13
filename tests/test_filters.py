# -*- coding: utf-8 -*-
"""
    unit test for the filters
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Missing tests:

    -   wordcount
    -   rst
    -   markdown
    -   textile

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

CAPITALIZE = '''{{ "foo bar"|capitalize }}'''
CENTER = '''{{ "foo"|center(9) }}'''
DEFAULT = '''{{ missing|default("no") }}|{{ false|default('no') }}|\
{{ false|default('no', true) }}|{{ given|default("no") }}'''
DICTSORT = '''{{ foo|dictsort }}|\
{{ foo|dictsort(true) }}|\
{{ foo|dictsort(false, 'value') }}'''
BATCH = '''{{ foo|batch(3) }}|{{ foo|batch(3, 'X') }}'''
SLICE = '''{{ foo|slice(3) }}|{{ foo|slice(3, 'X') }}'''
ESCAPE = '''{{ '<">&'|escape }}|{{ '<">&'|escape(true) }}'''
STRIPTAGS = '''{{ foo|striptags }}'''
FILESIZEFORMAT = '{{ 100|filesizeformat }}|\
{{ 1000|filesizeformat }}|\
{{ 1000000|filesizeformat }}|\
{{ 1000000000|filesizeformat }}|\
{{ 1000000000000|filesizeformat }}'
FIRST = '''{{ foo|first }}'''
FLOAT = '''{{ "42"|float }}|{{ "ajsghasjgd"|float }}|{{ "32.32"|float }}'''
FORMAT = '''{{ "%s|%s"|format("a", "b") }}'''
INDENT = '''{{ foo|indent(2) }}|{{ foo|indent(2, true) }}'''
INT = '''{{ "42"|int }}|{{ "ajsghasjgd"|int }}|{{ "32.32"|int }}'''
JOIN = '''{{ [1, 2, 3]|join("|") }}'''
LAST = '''{{ foo|last }}'''
LENGTH = '''{{ "hello world"|length }}'''
LOWER = '''{{ "FOO"|lower }}'''
PPRINT = '''{{ data|pprint }}'''
RANDOM = '''{{ seq|random }}'''
REVERSE = '''{{ "foobar"|reverse }}|{{ [1, 2, 3]|reverse }}'''
STRING = '''{{ range(10)|string }}'''
TITLE = '''{{ "foo bar"|title }}'''
TRIM = '''{{ "      foo       "|trim }}'''
TRUNCATE = '''{{ data|truncate(15, true, ">>>") }}|\
{{ data|truncate(15, false, ">>>") }}|\
{{ smalldata|truncate(15) }}'''
UPPER = '''{{ "foo"|upper }}'''
URLENCODE = '''{{ "f#b"|urlencode }}'''
URLIZE = '''{{ "foo http://www.example.com/ bar"|urlize }}'''
WORDCOUNT = '''{{ "foo bar baz"|wordcount }}'''
BLOCK = '''{% filter lower|escape %}<HEHE>{% endfilter %}'''
CHAINING = '''{{ ['<foo>', '<bar>']|first|upper|escape }}'''
SUM = '''{{ [1, 2, 3, 4, 5, 6]|sum }}'''
ABS = '''{{ -1|abs }}|{{ 1|abs }}'''
ROUND = '''{{ 2.7|round }}|{{ 2.1|round }}|\
{{ 2.1234|round(2, 'floor') }}|{{ 2.1|round(0, 'ceil') }}'''
XMLATTR = '''{{ {'foo': 42, 'bar': 23, 'fish': none,
'spam': missing, 'blub:blub': '<?>'}|xmlattr }}'''
SORT = '''{{ [2, 3, 1]|sort }}|{{ [2, 3, 1]|sort(true) }}'''
GROUPBY = '''{{ [{'foo': 1, 'bar': 2},
                 {'foo': 2, 'bar': 3},
                 {'foo': 1, 'bar': 1},
                 {'foo': 3, 'bar': 4}]|groupby('foo') }}'''
FILTERTAG = '''{% filter upper|replace('FOO', 'foo') %}foobar{% endfilter %}'''



def test_capitalize(env):
    tmpl = env.from_string(CAPITALIZE)
    assert tmpl.render() == 'Foo bar'


def test_center(env):
    tmpl = env.from_string(CENTER)
    assert tmpl.render() == '   foo   '


def test_default(env):
    tmpl = env.from_string(DEFAULT)
    assert tmpl.render(given='yes') == 'no|False|no|yes'


def test_dictsort(env):
    tmpl = env.from_string(DICTSORT)
    out = tmpl.render(foo={"a": 0, "b": 1, "c": 2, "A": 3})
    assert out == ("[('a', 0), ('A', 3), ('b', 1), ('c', 2)]|"
                   "[('A', 3), ('a', 0), ('b', 1), ('c', 2)]|"
                   "[('a', 0), ('b', 1), ('c', 2), ('A', 3)]")


def test_batch(env):
    tmpl = env.from_string(BATCH)
    out = tmpl.render(foo=range(10))
    assert out == ("[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]|"
                   "[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 'X', 'X']]")


def test_slice(env):
    tmpl = env.from_string(SLICE)
    out = tmpl.render(foo=range(10))
    assert out == ("[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]|"
                   "[[0, 1, 2, 3], [4, 5, 6, 'X'], [7, 8, 9, 'X']]")


def test_escape(env):
    tmpl = env.from_string(ESCAPE)
    out = tmpl.render()
    assert out == '&lt;&quot;&gt;&amp;|&lt;&quot;&gt;&amp;'


def test_striptags(env):
    tmpl = env.from_string(STRIPTAGS)
    out = tmpl.render(foo='  <p>just a small   \n <a href="#">'
                      'example</a> link</p>\n<p>to a webpage</p> '
                      '<!-- <p>and some commented stuff</p> -->')
    assert out == 'just a small example link to a webpage'


def test_filesizeformat(env):
    tmpl = env.from_string(FILESIZEFORMAT)
    out = tmpl.render()
    assert out == '100 Bytes|1000 Bytes|976.6 KB|953.7 MB|931.3 GB'


def test_first(env):
    tmpl = env.from_string(FIRST)
    out = tmpl.render(foo=range(10))
    assert out == '0'


def test_float(env):
    tmpl = env.from_string(FLOAT)
    out = tmpl.render()
    assert out == '42.0|0.0|32.32'


def test_format(env):
    tmpl = env.from_string(FORMAT)
    out = tmpl.render()
    assert out == 'a|b'


def test_indent(env):
    tmpl = env.from_string(INDENT)
    text = '\n'.join([' '.join(['foo', 'bar'] * 2)] * 2)
    out = tmpl.render(foo=text)
    assert out == 'foo bar foo bar\n  foo bar foo bar|  ' \
                  'foo bar foo bar\n  foo bar foo bar'


def test_int(env):
    tmpl = env.from_string(INT)
    out = tmpl.render()
    assert out == '42|0|32'


def test_join(env):
    tmpl = env.from_string(JOIN)
    out = tmpl.render()
    assert out == '1|2|3'


def test_last(env):
    tmpl = env.from_string(LAST)
    out = tmpl.render(foo=range(10))
    assert out == '9'


def test_length(env):
    tmpl = env.from_string(LENGTH)
    out = tmpl.render()
    assert out == '11'


def test_lower(env):
    tmpl = env.from_string(LOWER)
    out = tmpl.render()
    assert out == 'foo'


def test_pprint(env):
    from pprint import pformat
    tmpl = env.from_string(PPRINT)
    data = range(1000)
    assert tmpl.render(data=data) == pformat(data)


def test_random(env):
    tmpl = env.from_string(RANDOM)
    seq = range(100)
    for _ in range(10):
        assert int(tmpl.render(seq=seq)) in seq


def test_reverse(env):
    tmpl = env.from_string(REVERSE)
    assert tmpl.render() == 'raboof|[3, 2, 1]'


def test_string(env):
    tmpl = env.from_string(STRING)
    assert tmpl.render(foo=range(10)) == str(range(10))


def test_title(env):
    tmpl = env.from_string(TITLE)
    assert tmpl.render() == "Foo Bar"


def test_truncate(env):
    tmpl = env.from_string(TRUNCATE)
    assert tmpl.render() == 'foo'


def test_truncate(env):
    tmpl = env.from_string(TRUNCATE)
    out = tmpl.render(data='foobar baz bar' * 1000,
                      smalldata='foobar baz bar')
    assert out == 'foobar baz barf>>>|foobar baz >>>|foobar baz bar'


def test_upper(env):
    tmpl = env.from_string(UPPER)
    assert tmpl.render() == 'FOO'


def test_urlencode(env):
    tmpl = env.from_string(URLENCODE)
    assert tmpl.render() == 'f%23b'


def test_urlize(env):
    tmpl = env.from_string(URLIZE)
    assert tmpl.render() == 'foo <a href="http://www.example.com/">'\
                            'http://www.example.com/</a> bar'


def test_wordcount(env):
    tmpl = env.from_string(WORDCOUNT)
    assert tmpl.render() == '3'


def test_block(env):
    tmpl = env.from_string(BLOCK)
    assert tmpl.render() == '&lt;hehe&gt;'


def test_chaining(env):
    tmpl = env.from_string(CHAINING)
    assert tmpl.render() == '&lt;FOO&gt;'


def test_sum(env):
    tmpl = env.from_string(SUM)
    assert tmpl.render() == '21'


def test_abs(env):
    tmpl = env.from_string(ABS)
    return tmpl.render() == '1|1'


def test_round(env):
    tmpl = env.from_string(ROUND)
    return tmpl.render() == '3.0|2.0|2.1|3.0'


def test_xmlattr(env):
    tmpl = env.from_string(XMLATTR)
    out = tmpl.render().split()
    assert len(out) == 3
    assert 'foo="42"' in out
    assert 'bar="23"' in out
    assert 'blub:blub="&lt;?&gt;"' in out


def test_sort(env):
    tmpl = env.from_string(SORT)
    assert tmpl.render() == '[1, 2, 3]|[3, 2, 1]'


def test_groupby(env):
    tmpl = env.from_string(GROUPBY)
    assert tmpl.render() == (
        "[{'list': [{'foo': 1, 'bar': 2}, {'foo': 1, 'bar': 1}], "
        "'grouper': 1}, {'list': [{'foo': 2, 'bar': 3}], 'grouper': 2}, "
        "{'list': [{'foo': 3, 'bar': 4}], 'grouper': 3}]"
    )


def test_filtertag(env):
    tmpl = env.from_string(FILTERTAG)
    assert tmpl.render() == 'fooBAR'
