# -*- coding: utf-8 -*-
"""
    unit test for the lexer
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

BALANCING = '''{% for item in seq %}${{'foo': item}|upper}{% endfor %}'''
COMMENTS = '''\
<ul>
<!--- for item in seq -->
  <li>{item}</li>
<!--- endfor -->
</ul>'''
BYTEFALLBACK = u'''{{ 'foo'|pprint }}|{{ 'bär'|pprint }}'''


def test_balancing():
    from jinja import Environment
    env = Environment('{%', '%}', '${', '}')
    tmpl = env.from_string(BALANCING)
    assert tmpl.render(seq=range(3)) == "{'FOO': 0}{'FOO': 1}{'FOO': 2}"


def test_comments():
    from jinja import Environment
    env = Environment('<!--', '-->', '{', '}')
    tmpl = env.from_string(COMMENTS)
    assert tmpl.render(seq=range(3)) == ("<ul>\n  <li>0</li>\n  "
                                         "<li>1</li>\n  <li>2</li>\n</ul>")


def test_string_escapes(env):
    for char in u'\0', u'\u2668', u'\xe4', u'\t', u'\r', u'\n':
        tmpl = env.from_string('{{ %s }}' % repr(char)[1:])
        assert tmpl.render() == char
    assert env.from_string('{{ "\N{HOT SPRINGS}" }}').render() == u'\u2668'


def test_bytefallback(env):
    tmpl = env.from_string(BYTEFALLBACK)
    assert tmpl.render() == u"'foo'|u'b\\xe4r'"


def test_operators(env):
    from jinja.lexer import operators
    for test, expect in operators.iteritems():
        if test in '([{}])':
            continue
        stream = env.lexer.tokenize('{{ %s }}' % test)
        stream.next()
        assert stream.current.type == expect
