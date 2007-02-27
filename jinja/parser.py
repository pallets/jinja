# -*- coding: utf-8 -*-
"""
    jinja.parser
    ~~~~~~~~~~~~

    Implements the template parser.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from compiler import ast, parse
from jinja import nodes
from jinja.datastructure import TokenStream
from jinja.exceptions import TemplateSyntaxError


# callback functions for the subparse method
end_of_block = lambda p, t, d: t == 'block_end'
end_of_variable = lambda p, t, d: t == 'variable_end'
switch_for = lambda p, t, d: t == 'name' and d in ('else', 'endfor')
end_of_for = lambda p, t, d: t == 'name' and d == 'endfor'
switch_if = lambda p, t, d: t == 'name' and d in ('else', 'endif')
end_of_if = lambda p, t, d: t == 'name' and d == 'endif'


class Parser(object):
    """
    The template parser class.

    Transforms sourcecode into an abstract syntax tree::

        >>> parse("{% for item in seq|reversed %}{{ item }}{% endfor %}")
        Document(ForLoop(AssignName('item'), Filter(Name('seq'), Name('reversed')),
                         Print('item'), None))
        >>> parse("{% if true %}foo{% else %}bar{% endif %}")
        Document(IfCondition(Name('true'), Data('foo'), Data('bar')))
        >>> parse("{% if false %}...{% elif 0 > 1 %}...{% else %}...{% endif %}")
        Document(IfCondition(Name('false'), Data('...'),
                             IfCondition(Compare('>', Const(0), Const(1)),
                                         Data('...'), Data('...'))))
    """

    def __init__(self, environment, source, filename=None):
        self.environment = environment
        if isinstance(source, str):
            source = source.decode(environment.template_charset, 'ignore')
        self.source = source
        self.filename = filename
        self.tokenstream = environment.lexer.tokenize(source)
        self._parsed = False

        self.directives = {
            'for':          self.handle_for_directive,
            'if':           self.handle_if_directive,
            'cycle':        self.handle_cycle_directive,
            'print':        self.handle_print_directive
        }

    def handle_for_directive(self, pos, gen):
        """
        Handle a for directive and return a ForLoop node
        """
        ast = self.parse_python(pos, gen, 'for %s:pass\nelse:pass')
        body = self.subparse(switch_for)

        # do we have an else section?
        if self.tokenstream.next()[2] == 'else':
            self.close_remaining_block()
            else_ = self.subparse(end_of_for, True)
        else:
            else_ = None
        self.close_remaining_block()

        return nodes.ForLoop(pos, ast.assign, ast.list, body, else_)

    def handle_if_directive(self, pos, gen):
        """
        Handle if/else blocks. elif is not supported by now.
        """
        ast = self.parse_python(pos, gen, 'if %s:pass\nelse:pass')
        body = self.subparse(switch_if)

        # do we have an else section?
        if self.tokenstream.next()[2] == 'else':
            self.close_remaining_block()
            else_ = self.subparse(end_of_if, True)
        else:
            else_ = None
        self.close_remaining_block()

        return nodes.IfCondition(pos, ast.tests[0][0], body, else_)

    def handle_cycle_directive(self, pos, gen):
        """
        Handle {% cycle foo, bar, baz %}.
        """
        ast = self.parse_python(pos, gen, '_cycle((%s))')
        # ast is something like Discard(CallFunc(Name('_cycle'), ...))
        # skip that.
        return nodes.Cycle(pos, ast.expr.args[0])

    def handle_print_directive(self, pos, gen):
        """
        Handle {{ foo }} and {% print foo %}.
        """
        ast = self.parse_python(pos, gen, 'print_(%s)')
        # ast is something like Discard(CallFunc(Name('print_'), ...))
        # so just use the args
        arguments = ast.expr.args
        # we only accept one argument
        if len(arguments) != 1:
            raise TemplateSyntaxError('invalid argument count for print; '
                                      'print requires exactly one argument, '
                                      'got %d.' % len(arguments), pos)
        return nodes.Print(pos, arguments[0])

    def parse_python(self, pos, gen, template='%s'):
        """
        Convert the passed generator into a flat string representing
        python sourcecode and return an ast node or raise a
        TemplateSyntaxError.
        """
        tokens = []
        for t_pos, t_token, t_data in gen:
            if t_token == 'string':
                tokens.append('u' + t_data)
            else:
                tokens.append(t_data)
        source = '\xef\xbb\xbf' + (template % (u' '.join(tokens)).encode('utf-8'))
        try:
            ast = parse(source, 'exec')
        except SyntaxError, e:
            raise TemplateSyntaxError(str(e), pos + e.offset - 1)
        assert len(ast.node.nodes) == 1, 'get %d nodes, 1 expected' % len(ast.node.nodes)
        return ast.node.nodes[0]

    def parse(self):
        """
        Parse the template and return a nodelist.
        """
        return self.subparse(None)

    def subparse(self, test, drop_needle=False):
        """
        Helper function used to parse the sourcecode until the test
        function which is passed a tuple in the form (pos, token, data)
        returns True. In that case the current token is pushed back to
        the tokenstream and the generator ends.

        The test function is only called for the first token after a
        block tag. Variable tags are *not* aliases for {% print %} in
        that case.

        If drop_needle is True the needle_token is removed from the tokenstream.
        """
        def finish():
            """Helper function to remove unused nodelists."""
            if len(result) == 1:
                return result[0]
            return result

        pos = self.tokenstream.last[0]
        result = nodes.NodeList(pos)
        for pos, token, data in self.tokenstream:
            # this token marks the begin or a variable section.
            # parse everything till the end of it.
            if token == 'variable_begin':
                gen = self.tokenstream.fetch_until(end_of_variable, True)
                result.append(self.directives['print'](pos, gen))

            # this token marks the start of a block. like for variables
            # just parse everything until the end of the block
            elif token == 'block_begin':
                gen = self.tokenstream.fetch_until(end_of_block, True)
                try:
                    pos, token, data = gen.next()
                except StopIteration:
                    raise TemplateSyntaxError('unexpected end of block', pos)

                # first token *must* be a name token
                if token != 'name':
                    raise TemplateSyntaxError('unexpected %r token' % token, pos)

                # if a test function is passed to subparse we check if we
                # reached the end of such a requested block.
                if test is not None and test(pos, token, data):
                    if not drop_needle:
                        self.tokenstream.push(pos, token, data)
                    return finish()

                # the first token tells us which directive we want to call.
                # if if doesn't match any existing directive it's like a
                # template syntax error.
                if data in self.directives:
                    node = self.directives[data](pos, gen)
                else:
                    raise TemplateSyntaxError('unknown directive %r' % data, pos)
                result.append(node)

            # here the only token we should get is "data". all other
            # tokens just exist in block or variable sections. (if the
            # tokenizer is not brocken)
            elif token == 'data':
                result.append(nodes.Text(pos, data))

            # so this should be unreachable code
            else:
                raise AssertionError('unexpected token %r' % token)

        # still here and a test function is provided? raise and error
        if test is not None:
            raise TemplateSyntaxError('unexpected end of template', pos)
        return finish()

    def close_remaining_block(self):
        """
        If we opened a block tag because one of our tags requires an end
        tag we can use this method to drop the rest of the block from
        the stream. If the next token isn't the block end we throw an
        error.
        """
        pos = self.tokenstream.last[0]
        try:
            pos, token, data = self.tokenstream.next()
        except StopIteration:
            raise TemplateSyntaxError('missing closing tag', pos)
        if token != 'block_end':
            raise TemplateSyntaxError('expected close tag, found %r' % token, pos)
