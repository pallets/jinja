# -*- coding: utf-8 -*-
"""
    unit test for the parser
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, Template, TemplateSyntaxError

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


def test_error_messages():
    def assert_error(code, expected):
        try:
            Template(code)
        except TemplateSyntaxError, e:
            assert str(e) == expected, 'unexpected error message'
        else:
            assert False, 'that was suposed to be an error'

    assert_error('{% for item in seq %}...{% endif %}',
                 "Encountered unknown tag 'endif'. Jinja was looking "
                 "for the following tags: 'endfor' or 'else'. The "
                 "innermost block that needs to be closed is 'for'.")
    assert_error('{% if foo %}{% for item in seq %}...{% endfor %}{% endfor %}',
                 "Encountered unknown tag 'endfor'. Jinja was looking for "
                 "the following tags: 'elif' or 'else' or 'endif'. The "
                 "innermost block that needs to be closed is 'if'.")
    assert_error('{% if foo %}',
                 "Unexpected end of template. Jinja was looking for the "
                 "following tags: 'elif' or 'else' or 'endif'. The "
                 "innermost block that needs to be closed is 'if'.")
    assert_error('{% for item in seq %}',
                 "Unexpected end of template. Jinja was looking for the "
                 "following tags: 'endfor' or 'else'. The innermost block "
                 "that needs to be closed is 'for'.")
