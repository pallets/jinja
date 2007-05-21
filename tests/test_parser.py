# -*- coding: utf-8 -*-
"""
    unit test for the parser
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from jinja import Environment

NO_VARIABLE_BLOCK = '''\
{# i'm a freaking comment #}\
{% if foo %}{% foo %}{% endif %}
{% for item in seq %}{% item %}{% endfor %}
{% trans foo %}foo is {% foo %}{% endtrans %}
{% trans foo %}one foo{% pluralize %}{% foo %} foos{% endtrans %}'''

PHP_SYNTAX = '''\
<!-- I'm a comment, I'm not interesting -->\
<? for item in seq -?>
    <?= item ?>
<?- endfor ?>'''

ERB_SYNTAX = '''\
<%# I'm a comment, I'm not interesting %>\
<% for item in seq -%>
    <%= item %>
<%- endfor %>'''

COMMENT_SYNTAX = '''\
<!--# I'm a comment, I'm not interesting -->\
<!-- for item in seq --->
    ${item}
<!--- endfor -->'''

SMARTY_SYNTAX = '''\
{* I'm a comment, I'm not interesting *}\
{for item in seq-}
    {item}
{-endfor}'''


def test_no_variable_block():
    env = Environment('{%', '%}', None, None)
    tmpl = env.from_string(NO_VARIABLE_BLOCK)
    assert tmpl.render(foo=42, seq=range(2)).splitlines() == [
        '42',
        '01',
        'foo is 42',
        '42 foos'
    ]


def test_php_syntax():
    env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->')
    tmpl = env.from_string(PHP_SYNTAX)
    assert tmpl.render(seq=range(5)) == '01234'


def test_erb_syntax():
    env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>')
    tmpl = env.from_string(ERB_SYNTAX)
    assert tmpl.render(seq=range(5)) == '01234'


def test_comment_syntax():
    env = Environment('<!--', '-->', '${', '}', '<!--#', '-->')
    tmpl = env.from_string(COMMENT_SYNTAX)
    assert tmpl.render(seq=range(5)) == '01234'


def test_smarty_syntax():
    env = Environment('{', '}', '{', '}', '{*', '*}')
    tmpl = env.from_string(SMARTY_SYNTAX)
    assert tmpl.render(seq=range(5)) == '01234'
