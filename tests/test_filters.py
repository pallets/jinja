# -*- coding: utf-8 -*-
"""
    unit test for the filters
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Markup, Environment

env = Environment()


CAPITALIZE = '''{{ "foo bar"|capitalize }}'''
CENTER = '''{{ "foo"|center(9) }}'''
DEFAULT = '''{{ missing|default("no") }}|{{ false|default('no') }}|\
{{ false|default('no', true) }}|{{ given|default("no") }}'''
DICTSORT = '''{{ foo|dictsort }}|\
{{ foo|dictsort(true) }}|\
{{ foo|dictsort(false, 'value') }}'''
BATCH = '''{{ foo|batch(3)|list }}|{{ foo|batch(3, 'X')|list }}'''
SLICE = '''{{ foo|slice(3)|list }}|{{ foo|slice(3, 'X')|list }}'''
ESCAPE = '''{{ '<">&'|escape }}'''
STRIPTAGS = '''{{ foo|striptags }}'''
FILESIZEFORMAT = '{{ 100|filesizeformat }}|\
{{ 1000|filesizeformat }}|\
{{ 1000000|filesizeformat }}|\
{{ 1000000000|filesizeformat }}|\
{{ 1000000000000|filesizeformat }}|\
{{ 100|filesizeformat(true) }}|\
{{ 1000|filesizeformat(true) }}|\
{{ 1000000|filesizeformat(true) }}|\
{{ 1000000000|filesizeformat(true) }}|\
{{ 1000000000000|filesizeformat(true) }}'
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
REVERSE = '''{{ "foobar"|reverse|join }}|{{ [1, 2, 3]|reverse|list }}'''
STRING = '''{{ range(10)|string }}'''
TITLE = '''{{ "foo bar"|title }}'''
TRIM = '''{{ "      foo       "|trim }}'''
TRUNCATE = '''{{ data|truncate(15, true, ">>>") }}|\
{{ data|truncate(15, false, ">>>") }}|\
{{ smalldata|truncate(15) }}'''
UPPER = '''{{ "foo"|upper }}'''
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
SORT1 = '''{{ [2, 3, 1]|sort }}|{{ [2, 3, 1]|sort(true) }}'''
GROUPBY = '''{% for grouper, list in [{'foo': 1, 'bar': 2},
                 {'foo': 2, 'bar': 3},
                 {'foo': 1, 'bar': 1},
                 {'foo': 3, 'bar': 4}]|groupby('foo') -%}
{{ grouper }}: {{ list|join(', ') }}
{% endfor %}'''
FILTERTAG = '''{% filter upper|replace('FOO', 'foo') %}foobar{% endfilter %}'''
SORT2 = '''{{ ['foo', 'Bar', 'blah']|sort }}'''


def test_capitalize():
    tmpl = env.from_string(CAPITALIZE)
    assert tmpl.render() == 'Foo bar'


def test_center():
    tmpl = env.from_string(CENTER)
    assert tmpl.render() == '   foo   '


def test_default():
    tmpl = env.from_string(DEFAULT)
    assert tmpl.render(given='yes') == 'no|False|no|yes'


def test_dictsort():
    tmpl = env.from_string(DICTSORT)
    out = tmpl.render(foo={"aa": 0, "b": 1, "c": 2, "AB": 3})
    assert out == ("[('aa', 0), ('AB', 3), ('b', 1), ('c', 2)]|"
                   "[('AB', 3), ('aa', 0), ('b', 1), ('c', 2)]|"
                   "[('aa', 0), ('b', 1), ('c', 2), ('AB', 3)]")


def test_batch():
    tmpl = env.from_string(BATCH)
    out = tmpl.render(foo=range(10))
    assert out == ("[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]|"
                   "[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 'X', 'X']]")


def test_slice():
    tmpl = env.from_string(SLICE)
    out = tmpl.render(foo=range(10))
    assert out == ("[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]|"
                   "[[0, 1, 2, 3], [4, 5, 6, 'X'], [7, 8, 9, 'X']]")


def test_escape():
    tmpl = env.from_string(ESCAPE)
    out = tmpl.render()
    assert out == '&lt;&#34;&gt;&amp;'


def test_striptags():
    tmpl = env.from_string(STRIPTAGS)
    out = tmpl.render(foo='  <p>just a small   \n <a href="#">'
                      'example</a> link</p>\n<p>to a webpage</p> '
                      '<!-- <p>and some commented stuff</p> -->')
    assert out == 'just a small example link to a webpage'


def test_filesizeformat():
    tmpl = env.from_string(FILESIZEFORMAT)
    out = tmpl.render()
    assert out == (
        '100 Bytes|1.0 KB|1.0 MB|1.0 GB|1000.0 GB|'
        '100 Bytes|1000 Bytes|976.6 KiB|953.7 MiB|931.3 GiB'
    )


def test_first():
    tmpl = env.from_string(FIRST)
    out = tmpl.render(foo=range(10))
    assert out == '0'


def test_float():
    tmpl = env.from_string(FLOAT)
    out = tmpl.render()
    assert out == '42.0|0.0|32.32'


def test_format():
    tmpl = env.from_string(FORMAT)
    out = tmpl.render()
    assert out == 'a|b'


def test_indent():
    tmpl = env.from_string(INDENT)
    text = '\n'.join([' '.join(['foo', 'bar'] * 2)] * 2)
    out = tmpl.render(foo=text)
    assert out == ('foo bar foo bar\n  foo bar foo bar|  '
                   'foo bar foo bar\n  foo bar foo bar')


def test_int():
    tmpl = env.from_string(INT)
    out = tmpl.render()
    assert out == '42|0|32'


def test_join():
    tmpl = env.from_string(JOIN)
    out = tmpl.render()
    assert out == '1|2|3'

    env2 = Environment(autoescape=True)
    tmpl = env2.from_string('{{ ["<foo>", "<span>foo</span>"|safe]|join }}')
    assert tmpl.render() == '&lt;foo&gt;<span>foo</span>'


def test_last():
    tmpl = env.from_string(LAST)
    out = tmpl.render(foo=range(10))
    assert out == '9'


def test_length():
    tmpl = env.from_string(LENGTH)
    out = tmpl.render()
    assert out == '11'


def test_lower():
    tmpl = env.from_string(LOWER)
    out = tmpl.render()
    assert out == 'foo'


def test_pprint():
    from pprint import pformat
    tmpl = env.from_string(PPRINT)
    data = range(1000)
    assert tmpl.render(data=data) == pformat(data)


def test_random():
    tmpl = env.from_string(RANDOM)
    seq = range(100)
    for _ in range(10):
        assert int(tmpl.render(seq=seq)) in seq


def test_reverse():
    tmpl = env.from_string(REVERSE)
    assert tmpl.render() == 'raboof|[3, 2, 1]'


def test_string():
    tmpl = env.from_string(STRING)
    assert tmpl.render(foo=range(10)) == unicode(xrange(10))


def test_title():
    tmpl = env.from_string(TITLE)
    assert tmpl.render() == "Foo Bar"


def test_truncate():
    tmpl = env.from_string(TRUNCATE)
    out = tmpl.render(data='foobar baz bar' * 1000,
                      smalldata='foobar baz bar')
    assert out == 'foobar baz barf>>>|foobar baz >>>|foobar baz bar'


def test_upper():
    tmpl = env.from_string(UPPER)
    assert tmpl.render() == 'FOO'


def test_urlize():
    tmpl = env.from_string(URLIZE)
    assert tmpl.render() == 'foo <a href="http://www.example.com/">'\
                            'http://www.example.com/</a> bar'


def test_wordcount():
    tmpl = env.from_string(WORDCOUNT)
    assert tmpl.render() == '3'


def test_block():
    tmpl = env.from_string(BLOCK)
    assert tmpl.render() == '&lt;hehe&gt;'


def test_chaining():
    tmpl = env.from_string(CHAINING)
    assert tmpl.render() == '&lt;FOO&gt;'


def test_sum():
    tmpl = env.from_string(SUM)
    assert tmpl.render() == '21'


def test_abs():
    tmpl = env.from_string(ABS)
    return tmpl.render() == '1|1'


def test_round():
    tmpl = env.from_string(ROUND)
    return tmpl.render() == '3.0|2.0|2.1|3.0'


def test_xmlattr():
    tmpl = env.from_string(XMLATTR)
    out = tmpl.render().split()
    assert len(out) == 3
    assert 'foo="42"' in out
    assert 'bar="23"' in out
    assert 'blub:blub="&lt;?&gt;"' in out


def test_sort1():
    tmpl = env.from_string(SORT1)
    assert tmpl.render() == '[1, 2, 3]|[3, 2, 1]'


def test_groupby():
    tmpl = env.from_string(GROUPBY)
    assert tmpl.render().splitlines() == [
        "1: {'foo': 1, 'bar': 2}, {'foo': 1, 'bar': 1}",
        "2: {'foo': 2, 'bar': 3}",
        "3: {'foo': 3, 'bar': 4}"
    ]


def test_filtertag():
    tmpl = env.from_string(FILTERTAG)
    assert tmpl.render() == 'fooBAR'


def test_replace():
    env = Environment()
    tmpl = env.from_string('{{ string|replace("o", 42) }}')
    assert tmpl.render(string='<foo>') == '<f4242>'

    env = Environment(autoescape=True)
    tmpl = env.from_string('{{ string|replace("o", 42) }}')
    assert tmpl.render(string='<foo>') == '&lt;f4242&gt;'
    tmpl = env.from_string('{{ string|replace("<", 42) }}')
    assert tmpl.render(string='<foo>') == '42foo&gt;'
    tmpl = env.from_string('{{ string|replace("o", ">x<") }}')
    assert tmpl.render(string=Markup('foo')) == 'f&gt;x&lt;&gt;x&lt;'


def test_forceescape():
    tmpl = env.from_string('{{ x|forceescape }}')
    assert tmpl.render(x=Markup('<div />')) == u'&lt;div /&gt;'


def test_safe():
    env = Environment(autoescape=True)
    tmpl = env.from_string('{{ "<div>foo</div>"|safe }}')
    assert tmpl.render() == '<div>foo</div>'
    tmpl = env.from_string('{{ "<div>foo</div>" }}')
    assert tmpl.render() == '&lt;div&gt;foo&lt;/div&gt;'


def test_sort2():
    assert env.from_string(SORT2).render() == "['Bar', 'blah', 'foo']"
