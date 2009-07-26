# -*- coding: utf-8 -*-
"""
    unit test for the lexer
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment

env = Environment()


RAW = '{% raw %}foo{% endraw %}|{%raw%}{{ bar }}|{% baz %}{%       endraw    %}'
BALANCING = '''{% for item in seq %}${{'foo': item}|upper}{% endfor %}'''
COMMENTS = '''\
<ul>
<!--- for item in seq -->
  <li>{item}</li>
<!--- endfor -->
</ul>'''
BYTEFALLBACK = u'''{{ 'foo'|pprint }}|{{ 'bär'|pprint }}'''


def test_raw():
    tmpl = env.from_string(RAW)
    assert tmpl.render() == 'foo|{{ bar }}|{% baz %}'


def test_balancing():
    from jinja2 import Environment
    env = Environment('{%', '%}', '${', '}')
    tmpl = env.from_string(BALANCING)
    assert tmpl.render(seq=range(3)) == "{'FOO': 0}{'FOO': 1}{'FOO': 2}"


def test_comments():
    from jinja2 import Environment
    env = Environment('<!--', '-->', '{', '}')
    tmpl = env.from_string(COMMENTS)
    assert tmpl.render(seq=range(3)) == ("<ul>\n  <li>0</li>\n  "
                                         "<li>1</li>\n  <li>2</li>\n</ul>")


def test_string_escapes():
    for char in u'\0', u'\u2668', u'\xe4', u'\t', u'\r', u'\n':
        tmpl = env.from_string('{{ %s }}' % repr(char)[1:])
        assert tmpl.render() == char
    assert env.from_string('{{ "\N{HOT SPRINGS}" }}').render() == u'\u2668'


def test_bytefallback():
    tmpl = env.from_string(BYTEFALLBACK)
    assert tmpl.render() == u"'foo'|u'b\\xe4r'"


def test_operators():
    from jinja2.lexer import operators
    for test, expect in operators.iteritems():
        if test in '([{}])':
            continue
        stream = env.lexer.tokenize('{{ %s }}' % test)
        stream.next()
        assert stream.current.type == expect


def test_normalizing():
    from jinja2 import Environment
    for seq in '\r', '\r\n', '\n':
        env = Environment(newline_sequence=seq)
        tmpl = env.from_string('1\n2\r\n3\n4\n')
        result = tmpl.render()
        assert result.replace(seq, 'X') == '1X2X3X4'
