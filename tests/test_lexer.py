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
