# -*- coding: utf-8 -*-
"""
    unit test for the parser
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment

env = Environment()


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

MAKO_SYNTAX = '''\
<%# regular comment %>
% for item in seq:
    ${item}
% endfor'''

MAKO_SYNTAX_LINECOMMENTS = '''\
<%# regular comment %>
% for item in seq:
    ${item} ## the rest of the stuff
% endfor'''

BALANCING = '''{{{'foo':'bar'}.foo}}'''

STARTCOMMENT = '''{# foo comment
and bar comment #}
{% macro blub() %}foo{% endmacro %}
{{ blub() }}'''

LINE_SYNTAX_PRIORITY1 = '''\
/* ignore me.
   I'm a multiline comment */
## for item in seq:
* ${item}          # this is just extra stuff
## endfor
'''

LINE_SYNTAX_PRIORITY2 = '''\
/* ignore me.
   I'm a multiline comment */
# for item in seq:
* ${item}          ## this is just extra stuff
    ## extra stuff i just want to ignore
# endfor
'''


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


def test_balancing():
    tmpl = env.from_string(BALANCING)
    assert tmpl.render() == 'bar'


def test_start_comment():
    tmpl = env.from_string(STARTCOMMENT)
    assert tmpl.render().strip() == 'foo'


def test_line_syntax():
    env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%')
    tmpl = env.from_string(MAKO_SYNTAX)
    assert [int(x.strip()) for x in tmpl.render(seq=range(5)).split()] == \
           range(5)

    env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##')
    tmpl = env.from_string(MAKO_SYNTAX_LINECOMMENTS)
    assert [int(x.strip()) for x in tmpl.render(seq=range(5)).split()] == \
            range(5)


def test_line_syntax_priority():
    # XXX: why is the whitespace there in front of the newline?
    env = Environment('{%', '%}', '${', '}', '/*', '*/', '##', '#')
    tmpl = env.from_string(LINE_SYNTAX_PRIORITY1)
    assert tmpl.render(seq=[1, 2]).strip() == '* 1\n* 2'
    env = Environment('{%', '%}', '${', '}', '/*', '*/', '#', '##')
    tmpl = env.from_string(LINE_SYNTAX_PRIORITY2)
    assert tmpl.render(seq=[1, 2]).strip() == '* 1\n\n* 2'
