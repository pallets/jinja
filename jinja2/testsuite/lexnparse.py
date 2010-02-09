# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.lexnparse
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    All the unittests regarding lexing, parsing and syntax.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import time
import tempfile
import unittest

from jinja2.testsuite import JinjaTestCase

from jinja2 import Environment, Template, TemplateSyntaxError

env = Environment()


class LexerTestCase(JinjaTestCase):

    def test_raw(self):
        tmpl = env.from_string('{% raw %}foo{% endraw %}|'
                               '{%raw%}{{ bar }}|{% baz %}{%       endraw    %}')
        assert tmpl.render() == 'foo|{{ bar }}|{% baz %}'

    def test_balancing(self):
        env = Environment('{%', '%}', '${', '}')
        tmpl = env.from_string('''{% for item in seq
            %}${{'foo': item}|upper}{% endfor %}''')
        assert tmpl.render(seq=range(3)) == "{'FOO': 0}{'FOO': 1}{'FOO': 2}"

    def test_comments(self):
        env = Environment('<!--', '-->', '{', '}')
        tmpl = env.from_string('''\
<ul>
<!--- for item in seq -->
  <li>{item}</li>
<!--- endfor -->
</ul>''')
        assert tmpl.render(seq=range(3)) == ("<ul>\n  <li>0</li>\n  "
                                             "<li>1</li>\n  <li>2</li>\n</ul>")

    def test_string_escapes(self):
        for char in u'\0', u'\u2668', u'\xe4', u'\t', u'\r', u'\n':
            tmpl = env.from_string('{{ %s }}' % repr(char)[1:])
            assert tmpl.render() == char
        assert env.from_string('{{ "\N{HOT SPRINGS}" }}').render() == u'\u2668'

    def test_bytefallback(self):
        tmpl = env.from_string(u'''{{ 'foo'|pprint }}|{{ 'bär'|pprint }}''')
        assert tmpl.render() == u"'foo'|u'b\\xe4r'"

    def test_operators(self):
        from jinja2.lexer import operators
        for test, expect in operators.iteritems():
            if test in '([{}])':
                continue
            stream = env.lexer.tokenize('{{ %s }}' % test)
            stream.next()
            assert stream.current.type == expect

    def test_normalizing(self):
        for seq in '\r', '\r\n', '\n':
            env = Environment(newline_sequence=seq)
            tmpl = env.from_string('1\n2\r\n3\n4\n')
            result = tmpl.render()
            assert result.replace(seq, 'X') == '1X2X3X4'


class ParserTestCase(JinjaTestCase):

    def test_php_syntax(self):
        env = Environment('<?', '?>', '<?=', '?>', '<!--', '-->')
        tmpl = env.from_string('''\
<!-- I'm a comment, I'm not interesting -->\
<? for item in seq -?>
    <?= item ?>
<?- endfor ?>''')
        assert tmpl.render(seq=range(5)) == '01234'

    def test_erb_syntax(self):
        env = Environment('<%', '%>', '<%=', '%>', '<%#', '%>')
        tmpl = env.from_string('''\
<%# I'm a comment, I'm not interesting %>\
<% for item in seq -%>
    <%= item %>
<%- endfor %>''')
        assert tmpl.render(seq=range(5)) == '01234'

    def test_comment_syntax(self):
        env = Environment('<!--', '-->', '${', '}', '<!--#', '-->')
        tmpl = env.from_string('''\
<!--# I'm a comment, I'm not interesting -->\
<!-- for item in seq --->
    ${item}
<!--- endfor -->''')
        assert tmpl.render(seq=range(5)) == '01234'

    def test_balancing(self):
        tmpl = env.from_string('''{{{'foo':'bar'}.foo}}''')
        assert tmpl.render() == 'bar'

    def test_start_comment(self):
        tmpl = env.from_string('''{# foo comment
and bar comment #}
{% macro blub() %}foo{% endmacro %}
{{ blub() }}''')
        assert tmpl.render().strip() == 'foo'

    def test_line_syntax(self):
        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%')
        tmpl = env.from_string('''\
<%# regular comment %>
% for item in seq:
    ${item}
% endfor''')
        assert [int(x.strip()) for x in tmpl.render(seq=range(5)).split()] == \
               range(5)

        env = Environment('<%', '%>', '${', '}', '<%#', '%>', '%', '##')
        tmpl = env.from_string('''\
<%# regular comment %>
% for item in seq:
    ${item} ## the rest of the stuff
% endfor''')
        assert [int(x.strip()) for x in tmpl.render(seq=range(5)).split()] == \
                range(5)

    def test_line_syntax_priority(self):
        # XXX: why is the whitespace there in front of the newline?
        env = Environment('{%', '%}', '${', '}', '/*', '*/', '##', '#')
        tmpl = env.from_string('''\
/* ignore me.
   I'm a multiline comment */
## for item in seq:
* ${item}          # this is just extra stuff
## endfor''')
        assert tmpl.render(seq=[1, 2]).strip() == '* 1\n* 2'
        env = Environment('{%', '%}', '${', '}', '/*', '*/', '#', '##')
        tmpl = env.from_string('''\
/* ignore me.
   I'm a multiline comment */
# for item in seq:
* ${item}          ## this is just extra stuff
    ## extra stuff i just want to ignore
# endfor''')
        assert tmpl.render(seq=[1, 2]).strip() == '* 1\n\n* 2'

    def test_error_messages(self):
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
        assert_error('{% block foo-bar-baz %}',
                     "Block names in Jinja have to be valid Python identifiers "
                     "and may not contain hypens, use an underscore instead.")


class SyntaxTestCase(JinjaTestCase):
    pass


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LexerTestCase))
    suite.addTest(unittest.makeSuite(ParserTestCase))
    suite.addTest(unittest.makeSuite(SyntaxTestCase))
    return suite
