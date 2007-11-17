# -*- coding: utf-8 -*-
"""
    jinja.parser
    ~~~~~~~~~~~~

    Implements the template parser.

    The Jinja template parser is not a real parser but a combination of the
    python compiler package and some postprocessing. The tokens yielded by
    the lexer are used to separate template data and expressions. The
    expression tokens are then converted into strings again and processed
    by the python parser.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja import nodes
from jinja.datastructure import StateTest
from jinja.exceptions import TemplateSyntaxError
from jinja.utils import set


__all__ = ['Parser']


# general callback functions for the parser
end_of_block = StateTest.expect_token('block_end',
                                      msg='expected end of block tag')
end_of_variable = StateTest.expect_token('variable_end',
                                         msg='expected end of variable')
end_of_comment = StateTest.expect_token('comment_end',
                                        msg='expected end of comment')

# internal tag callbacks
switch_for = StateTest.expect_token('else', 'endfor')
end_of_for = StateTest.expect_token('endfor')
switch_if = StateTest.expect_token('else', 'elif', 'endif')
end_of_if = StateTest.expect_token('endif')
end_of_filter = StateTest.expect_token('endfilter')
end_of_macro = StateTest.expect_token('endmacro')
end_of_call = StateTest.expect_token('endcall')
end_of_block_tag = StateTest.expect_token('endblock')
end_of_trans = StateTest.expect_token('endtrans')

# this ends a tuple
tuple_edge_tokens = set(['rparen', 'block_end', 'variable_end', 'in',
                         'recursive'])


class Parser(object):
    """
    The template parser class.

    Transforms sourcecode into an abstract syntax tree.
    """

    def __init__(self, environment, source, filename=None):
        self.environment = environment
        if isinstance(source, str):
            source = source.decode(environment.template_charset, 'ignore')
        if isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        self.source = source
        self.filename = filename
        self.closed = False

        #: set for blocks in order to keep them unique
        self.blocks = set()

        #: mapping of directives that require special treatment
        self.directives = {
            # "fake" directives that just trigger errors
            'raw':          self.parse_raw_directive,
            'extends':      self.parse_extends_directive,

            # real directives
            'for':          self.parse_for_loop,
            'if':           self.parse_if_condition,
            'cycle':        self.parse_cycle_directive,
            'call':         self.parse_call_directive,
            'set':          self.parse_set_directive,
            'filter':       self.parse_filter_directive,
            'print':        self.parse_print_directive,
            'macro':        self.parse_macro_directive,
            'block':        self.parse_block_directive,
            'include':      self.parse_include_directive,
            'trans':        self.parse_trans_directive
        }

        #: set of directives that are only available in a certain
        #: context.
        self.context_directives = set([
            'elif', 'else', 'endblock', 'endfilter', 'endfor', 'endif',
            'endmacro', 'endraw', 'endtrans', 'pluralize'
        ])

        #: get the `no_variable_block` flag
        self.no_variable_block = self.environment.lexer.no_variable_block

        self.stream = environment.lexer.tokenize(source, filename)

    def parse_raw_directive(self):
        """
        Handle fake raw directive. (real raw directives are handled by
        the lexer. But if there are arguments to raw or the end tag
        is missing the parser tries to resolve this directive. In that
        case present the user a useful error message.
        """
        if self.stream:
            raise TemplateSyntaxError('raw directive does not support '
                                      'any arguments.', self.stream.lineno,
                                      self.filename)
        raise TemplateSyntaxError('missing end tag for raw directive.',
                                  self.stream.lineno, self.filename)

    def parse_extends_directive(self):
        """
        Handle the extends directive used for inheritance.
        """
        raise TemplateSyntaxError('mispositioned extends tag. extends must '
                                  'be the first tag of a template.',
                                  self.stream.lineno, self.filename)

    def parse_for_loop(self):
        """
        Handle a for directive and return a ForLoop node
        """
        token = self.stream.expect('for')
        item = self.parse_tuple_expression(simplified=True)
        if not item.allows_assignments():
            raise TemplateSyntaxError('cannot assign to expression',
                                      token.lineno, self.filename)

        self.stream.expect('in')
        seq = self.parse_tuple_expression()
        if self.stream.current.type == 'recursive':
            self.stream.next()
            recursive = True
        else:
            recursive = False
        self.stream.expect('block_end')

        body = self.subparse(switch_for)

        # do we have an else section?
        if self.stream.current.type == 'else':
            self.stream.next()
            self.stream.expect('block_end')
            else_ = self.subparse(end_of_for, True)
        else:
            self.stream.next()
            else_ = None
        self.stream.expect('block_end')

        return nodes.ForLoop(item, seq, body, else_, recursive,
                             token.lineno, self.filename)

    def parse_if_condition(self):
        """
        Handle if/else blocks.
        """
        token = self.stream.expect('if')
        expr = self.parse_expression()
        self.stream.expect('block_end')
        tests = [(expr, self.subparse(switch_if))]
        else_ = None

        # do we have an else section?
        while True:
            if self.stream.current.type == 'else':
                self.stream.next()
                self.stream.expect('block_end')
                else_ = self.subparse(end_of_if, True)
            elif self.stream.current.type == 'elif':
                self.stream.next()
                expr = self.parse_expression()
                self.stream.expect('block_end')
                tests.append((expr, self.subparse(switch_if)))
                continue
            else:
                self.stream.next()
            break
        self.stream.expect('block_end')

        return nodes.IfCondition(tests, else_, token.lineno, self.filename)

    def parse_cycle_directive(self):
        """
        Handle {% cycle foo, bar, baz %}.
        """
        token = self.stream.expect('cycle')
        expr = self.parse_tuple_expression()
        self.stream.expect('block_end')
        return nodes.Cycle(expr, token.lineno, self.filename)

    def parse_set_directive(self):
        """
        Handle {% set foo = 'value of foo' %}.
        """
        token = self.stream.expect('set')
        name = self.stream.expect('name')
        self.test_name(name.value)
        self.stream.expect('assign')
        value = self.parse_expression()
        if self.stream.current.type == 'bang':
            self.stream.next()
            scope_local = False
        else:
            scope_local = True
        self.stream.expect('block_end')
        return nodes.Set(name.value, value, scope_local,
                         token.lineno, self.filename)

    def parse_filter_directive(self):
        """
        Handle {% filter foo|bar %} directives.
        """
        token = self.stream.expect('filter')
        filters = []
        while self.stream.current.type != 'block_end':
            if filters:
                self.stream.expect('pipe')
            token = self.stream.expect('name')
            args = []
            if self.stream.current.type == 'lparen':
                self.stream.next()
                while self.stream.current.type != 'rparen':
                    if args:
                        self.stream.expect('comma')
                    args.append(self.parse_expression())
                self.stream.expect('rparen')
            filters.append((token.value, args))
        self.stream.expect('block_end')
        body = self.subparse(end_of_filter, True)
        self.stream.expect('block_end')
        return nodes.Filter(body, filters, token.lineno, self.filename)

    def parse_print_directive(self):
        """
        Handle {% print foo %}.
        """
        token = self.stream.expect('print')
        expr = self.parse_tuple_expression()
        node = nodes.Print(expr, token.lineno, self.filename)
        self.stream.expect('block_end')
        return node

    def parse_macro_directive(self):
        """
        Handle {% macro foo bar, baz %} as well as
        {% macro foo(bar, baz) %}.
        """
        token = self.stream.expect('macro')
        macro_name = self.stream.expect('name')
        self.test_name(macro_name.value)
        if self.stream.current.type == 'lparen':
            self.stream.next()
            needle_token = 'rparen'
        else:
            needle_token = 'block_end'

        args = []
        while self.stream.current.type != needle_token:
            if args:
                self.stream.expect('comma')
            name = self.stream.expect('name').value
            self.test_name(name)
            if self.stream.current.type == 'assign':
                self.stream.next()
                default = self.parse_expression()
            else:
                default = None
            args.append((name, default))

        self.stream.next()
        if needle_token == 'rparen':
            self.stream.expect('block_end')

        body = self.subparse(end_of_macro, True)
        self.stream.expect('block_end')

        return nodes.Macro(macro_name.value, args, body, token.lineno,
                           self.filename)

    def parse_call_directive(self):
        """
        Handle {% call foo() %}...{% endcall %}
        """
        token = self.stream.expect('call')
        expr = self.parse_call_expression()
        self.stream.expect('block_end')
        body = self.subparse(end_of_call, True)
        self.stream.expect('block_end')
        return nodes.Call(expr, body, token.lineno, self.filename)

    def parse_block_directive(self):
        """
        Handle block directives used for inheritance.
        """
        token = self.stream.expect('block')
        name = self.stream.expect('name').value

        # check if this block does not exist by now.
        if name in self.blocks:
            raise TemplateSyntaxError('block %r defined twice' %
                                       name, token.lineno,
                                       self.filename)
        self.blocks.add(name)

        if self.stream.current.type != 'block_end':
            lineno = self.stream.lineno
            expr = self.parse_tuple_expression()
            node = nodes.Print(expr, lineno, self.filename)
            body = nodes.NodeList([node], lineno, self.filename)
            self.stream.expect('block_end')
        else:
            # otherwise parse the body and attach it to the block
            self.stream.expect('block_end')
            body = self.subparse(end_of_block_tag, True)
            self.stream.expect('block_end')
        return nodes.Block(name, body, token.lineno, self.filename)

    def parse_include_directive(self):
        """
        Handle the include directive used for template inclusion.
        """
        token = self.stream.expect('include')
        template = self.stream.expect('string').value
        self.stream.expect('block_end')
        return nodes.Include(template, token.lineno, self.filename)

    def parse_trans_directive(self):
        """
        Handle translatable sections.
        """
        trans_token = self.stream.expect('trans')

        # string based translations {% trans "foo" %}
        if self.stream.current.type == 'string':
            text = self.stream.expect('string')
            self.stream.expect('block_end')
            return nodes.Trans(text.value, None, None, None,
                               trans_token.lineno, self.filename)

        # block based translations
        replacements = {}
        plural_var = None

        while self.stream.current.type != 'block_end':
            if replacements:
                self.stream.expect('comma')
            name = self.stream.expect('name')
            if self.stream.current.type == 'assign':
                self.stream.next()
                value = self.parse_expression()
            else:
                value = nodes.NameExpression(name.value, name.lineno,
                                             self.filename)
            if name.value in replacements:
                raise TemplateSyntaxError('translation variable %r '
                                          'is defined twice' % name.value,
                                          name.lineno, self.filename)
            replacements[name.value] = value
            if plural_var is None:
                plural_var = name.value
        self.stream.expect('block_end')

        def process_variable():
            var_name = self.stream.expect('name')
            if var_name.value not in replacements:
                raise TemplateSyntaxError('unregistered translation variable'
                                          " '%s'." % var_name.value,
                                          var_name.lineno, self.filename)
            buf.append('%%(%s)s' % var_name.value)

        buf = singular = []
        plural = None

        while True:
            token = self.stream.current
            if token.type == 'data':
                buf.append(token.value.replace('%', '%%'))
                self.stream.next()
            elif token.type == 'variable_begin':
                self.stream.next()
                process_variable()
                self.stream.expect('variable_end')
            elif token.type == 'block_begin':
                self.stream.next()
                if plural is None and self.stream.current.type == 'pluralize':
                    self.stream.next()
                    if self.stream.current.type == 'name':
                        plural_var = self.stream.expect('name').value
                    plural = buf = []
                elif self.stream.current.type == 'endtrans':
                    self.stream.next()
                    self.stream.expect('block_end')
                    break
                else:
                    if self.no_variable_block:
                        process_variable()
                    else:
                        raise TemplateSyntaxError('blocks are not allowed '
                                                  'in trans tags',
                                                  self.stream.lineno,
                                                  self.filename)
                self.stream.expect('block_end')
            else:
                assert False, 'something very strange happened'

        singular = u''.join(singular)
        if plural is not None:
            plural = u''.join(plural)
        return nodes.Trans(singular, plural, plural_var, replacements,
                           trans_token.lineno, self.filename)

    def parse_expression(self):
        """
        Parse one expression from the stream.
        """
        return self.parse_conditional_expression()

    def parse_subscribed_expression(self):
        """
        Like parse_expression but parses slices too. Because this
        parsing function requires a border the two tokens rbracket
        and comma mark the end of the expression in some situations.
        """
        lineno = self.stream.lineno

        if self.stream.current.type == 'colon':
            self.stream.next()
            args = [None]
        else:
            node = self.parse_expression()
            if self.stream.current.type != 'colon':
                return node
            self.stream.next()
            args = [node]

        if self.stream.current.type == 'colon':
            args.append(None)
        elif self.stream.current.type not in ('rbracket', 'comma'):
            args.append(self.parse_expression())
        else:
            args.append(None)

        if self.stream.current.type == 'colon':
            self.stream.next()
            if self.stream.current.type not in ('rbracket', 'comma'):
                args.append(self.parse_expression())
            else:
                args.append(None)
        else:
            args.append(None)

        return nodes.SliceExpression(*(args + [lineno, self.filename]))

    def parse_conditional_expression(self):
        """
        Parse a conditional expression (foo if bar else baz)
        """
        lineno = self.stream.lineno
        expr1 = self.parse_or_expression()
        while self.stream.current.type == 'if':
            self.stream.next()
            expr2 = self.parse_or_expression()
            self.stream.expect('else')
            expr3 = self.parse_conditional_expression()
            expr1 = nodes.ConditionalExpression(expr2, expr1, expr3,
                                                lineno, self.filename)
            lineno = self.stream.lineno
        return expr1

    def parse_or_expression(self):
        """
        Parse something like {{ foo or bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_and_expression()
        while self.stream.current.type == 'or':
            self.stream.next()
            right = self.parse_and_expression()
            left = nodes.OrExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_and_expression(self):
        """
        Parse something like {{ foo and bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_compare_expression()
        while self.stream.current.type == 'and':
            self.stream.next()
            right = self.parse_compare_expression()
            left = nodes.AndExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_compare_expression(self):
        """
        Parse something like {{ foo == bar }}.
        """
        known_operators = set(['eq', 'ne', 'lt', 'lteq', 'gt', 'gteq', 'in'])
        lineno = self.stream.lineno
        expr = self.parse_add_expression()
        ops = []
        while True:
            if self.stream.current.type in known_operators:
                op = self.stream.current.type
                self.stream.next()
                ops.append([op, self.parse_add_expression()])
            elif self.stream.current.type == 'not' and \
                 self.stream.look().type == 'in':
                self.stream.skip(2)
                ops.append(['not in', self.parse_add_expression()])
            else:
                break
        if not ops:
            return expr
        return nodes.CompareExpression(expr, ops, lineno, self.filename)

    def parse_add_expression(self):
        """
        Parse something like {{ foo + bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_sub_expression()
        while self.stream.current.type == 'add':
            self.stream.next()
            right = self.parse_sub_expression()
            left = nodes.AddExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_sub_expression(self):
        """
        Parse something like {{ foo - bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_concat_expression()
        while self.stream.current.type == 'sub':
            self.stream.next()
            right = self.parse_concat_expression()
            left = nodes.SubExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_concat_expression(self):
        """
        Parse something like {{ foo ~ bar }}.
        """
        lineno = self.stream.lineno
        args = [self.parse_mul_expression()]
        while self.stream.current.type == 'tilde':
            self.stream.next()
            args.append(self.parse_mul_expression())
        if len(args) == 1:
            return args[0]
        return nodes.ConcatExpression(args, lineno, self.filename)

    def parse_mul_expression(self):
        """
        Parse something like {{ foo * bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_div_expression()
        while self.stream.current.type == 'mul':
            self.stream.next()
            right = self.parse_div_expression()
            left = nodes.MulExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_div_expression(self):
        """
        Parse something like {{ foo / bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_floor_div_expression()
        while self.stream.current.type == 'div':
            self.stream.next()
            right = self.parse_floor_div_expression()
            left = nodes.DivExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_floor_div_expression(self):
        """
        Parse something like {{ foo // bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_mod_expression()
        while self.stream.current.type == 'floordiv':
            self.stream.next()
            right = self.parse_mod_expression()
            left = nodes.FloorDivExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_mod_expression(self):
        """
        Parse something like {{ foo % bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_pow_expression()
        while self.stream.current.type == 'mod':
            self.stream.next()
            right = self.parse_pow_expression()
            left = nodes.ModExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_pow_expression(self):
        """
        Parse something like {{ foo ** bar }}.
        """
        lineno = self.stream.lineno
        left = self.parse_unary_expression()
        while self.stream.current.type == 'pow':
            self.stream.next()
            right = self.parse_unary_expression()
            left = nodes.PowExpression(left, right, lineno, self.filename)
            lineno = self.stream.lineno
        return left

    def parse_unary_expression(self):
        """
        Parse all kinds of unary expressions.
        """
        if self.stream.current.type == 'not':
            return self.parse_not_expression()
        elif self.stream.current.type == 'sub':
            return self.parse_neg_expression()
        elif self.stream.current.type == 'add':
            return self.parse_pos_expression()
        return self.parse_primary_expression()

    def parse_not_expression(self):
        """
        Parse something like {{ not foo }}.
        """
        token = self.stream.expect('not')
        node = self.parse_unary_expression()
        return nodes.NotExpression(node, token.lineno, self.filename)

    def parse_neg_expression(self):
        """
        Parse something like {{ -foo }}.
        """
        token = self.stream.expect('sub')
        node = self.parse_unary_expression()
        return nodes.NegExpression(node, token.lineno, self.filename)

    def parse_pos_expression(self):
        """
        Parse something like {{ +foo }}.
        """
        token = self.stream.expect('add')
        node = self.parse_unary_expression()
        return nodes.PosExpression(node, token.lineno, self.filename)

    def parse_primary_expression(self, parse_postfix=True):
        """
        Parse a primary expression such as a name or literal.
        """
        current = self.stream.current
        if current.type == 'name':
            if current.value in ('true', 'false'):
                node = self.parse_bool_expression()
            elif current.value == 'none':
                node = self.parse_none_expression()
            elif current.value == 'undefined':
                node = self.parse_undefined_expression()
            elif current.value == '_':
                node = self.parse_gettext_call()
            else:
                node = self.parse_name_expression()
        elif current.type in ('integer', 'float'):
            node = self.parse_number_expression()
        elif current.type == 'string':
            node = self.parse_string_expression()
        elif current.type == 'regex':
            node = self.parse_regex_expression()
        elif current.type == 'lparen':
            node = self.parse_paren_expression()
        elif current.type == 'lbracket':
            node = self.parse_list_expression()
        elif current.type == 'lbrace':
            node = self.parse_dict_expression()
        elif current.type == 'at':
            node = self.parse_set_expression()
        else:
            raise TemplateSyntaxError("unexpected token '%s'" %
                                      self.stream.current,
                                      self.stream.current.lineno,
                                      self.filename)
        if parse_postfix:
            node = self.parse_postfix_expression(node)
        return node

    def parse_tuple_expression(self, enforce=False, simplified=False):
        """
        Parse multiple expressions into a tuple. This can also return
        just one expression which is not a tuple. If you want to enforce
        a tuple, pass it enforce=True.
        """
        lineno = self.stream.lineno
        if simplified:
            parse = self.parse_primary_expression
        else:
            parse = self.parse_expression
        args = []
        is_tuple = False
        while True:
            if args:
                self.stream.expect('comma')
            if self.stream.current.type in tuple_edge_tokens:
                break
            args.append(parse())
            if self.stream.current.type == 'comma':
                is_tuple = True
            else:
                break
        if not is_tuple and args:
            if enforce:
                raise TemplateSyntaxError('tuple expected', lineno,
                                          self.filename)
            return args[0]
        return nodes.TupleExpression(args, lineno, self.filename)

    def parse_bool_expression(self):
        """
        Parse a boolean literal.
        """
        token = self.stream.expect('name')
        if token.value == 'true':
            value = True
        elif token.value == 'false':
            value = False
        else:
            raise TemplateSyntaxError("expected boolean literal",
                                      token.lineno, self.filename)
        return nodes.ConstantExpression(value, token.lineno, self.filename)

    def parse_none_expression(self):
        """
        Parse a none literal.
        """
        token = self.stream.expect('name', 'none')
        return nodes.ConstantExpression(None, token.lineno, self.filename)

    def parse_undefined_expression(self):
        """
        Parse an undefined literal.
        """
        token = self.stream.expect('name', 'undefined')
        return nodes.UndefinedExpression(token.lineno, self.filename)

    def parse_gettext_call(self):
        """
        parse {{ _('foo') }}.
        """
        # XXX: check if only one argument was passed and if
        # it is a string literal. Maybe that should become a special
        # expression anyway.
        token = self.stream.expect('name', '_')
        node = nodes.NameExpression(token.value, token.lineno, self.filename)
        return self.parse_call_expression(node)

    def parse_name_expression(self):
        """
        Parse any name.
        """
        token = self.stream.expect('name')
        self.test_name(token.value)
        return nodes.NameExpression(token.value, token.lineno, self.filename)

    def parse_number_expression(self):
        """
        Parse a number literal.
        """
        token = self.stream.current
        if token.type not in ('integer', 'float'):
            raise TemplateSyntaxError('integer or float literal expected',
                                      token.lineno, self.filename)
        self.stream.next()
        return nodes.ConstantExpression(token.value, token.lineno, self.filename)

    def parse_string_expression(self):
        """
        Parse a string literal.
        """
        token = self.stream.expect('string')
        return nodes.ConstantExpression(token.value, token.lineno, self.filename)

    def parse_regex_expression(self):
        """
        Parse a regex literal.
        """
        token = self.stream.expect('regex')
        return nodes.RegexExpression(token.value, token.lineno, self.filename)

    def parse_paren_expression(self):
        """
        Parse a parenthized expression.
        """
        self.stream.expect('lparen')
        try:
            return self.parse_tuple_expression()
        finally:
            self.stream.expect('rparen')

    def parse_list_expression(self):
        """
        Parse something like {{ [1, 2, "three"] }}
        """
        token = self.stream.expect('lbracket')
        items = []
        while self.stream.current.type != 'rbracket':
            if items:
                self.stream.expect('comma')
            if self.stream.current.type == 'rbracket':
                break
            items.append(self.parse_expression())
        self.stream.expect('rbracket')

        return nodes.ListExpression(items, token.lineno, self.filename)

    def parse_dict_expression(self):
        """
        Parse something like {{ {1: 2, 3: 4} }}
        """
        token = self.stream.expect('lbrace')
        items = []
        while self.stream.current.type != 'rbrace':
            if items:
                self.stream.expect('comma')
            if self.stream.current.type == 'rbrace':
                break
            key = self.parse_expression()
            self.stream.expect('colon')
            value = self.parse_expression()
            items.append((key, value))
        self.stream.expect('rbrace')

        return nodes.DictExpression(items, token.lineno, self.filename)

    def parse_set_expression(self):
        """
        Parse something like {{ @(1, 2, 3) }}.
        """
        token = self.stream.expect('at')
        self.stream.expect('lparen')
        items = []
        while self.stream.current.type != 'rparen':
            if items:
                self.stream.expect('comma')
            if self.stream.current.type == 'rparen':
                break
            items.append(self.parse_expression())
        self.stream.expect('rparen')

        return nodes.SetExpression(items, token.lineno, self.filename)

    def parse_postfix_expression(self, node):
        """
        Parse a postfix expression such as a filter statement or a
        function call.
        """
        while True:
            current = self.stream.current.type
            if current == 'dot' or current == 'lbracket':
                node = self.parse_subscript_expression(node)
            elif current == 'lparen':
                node = self.parse_call_expression(node)
            elif current == 'pipe':
                node = self.parse_filter_expression(node)
            elif current == 'is':
                node = self.parse_test_expression(node)
            else:
                break
        return node

    def parse_subscript_expression(self, node):
        """
        Parse a subscript statement. Gets attributes and items from an
        object.
        """
        lineno = self.stream.lineno
        if self.stream.current.type == 'dot':
            self.stream.next()
            token = self.stream.current
            if token.type in ('name', 'integer'):
                arg = nodes.ConstantExpression(token.value, token.lineno,
                                               self.filename)
            else:
                raise TemplateSyntaxError('expected name or number',
                                          token.lineno, self.filename)
            self.stream.next()
        elif self.stream.current.type == 'lbracket':
            self.stream.next()
            args = []
            while self.stream.current.type != 'rbracket':
                if args:
                    self.stream.expect('comma')
                args.append(self.parse_subscribed_expression())
            self.stream.expect('rbracket')
            if len(args) == 1:
                arg = args[0]
            else:
                arg = nodes.TupleExpression(args, lineno, self.filename)
        else:
            raise TemplateSyntaxError('expected subscript expression',
                                      self.lineno, self.filename)
        return nodes.SubscriptExpression(node, arg, lineno, self.filename)

    def parse_call_expression(self, node=None):
        """
        Parse a call.
        """
        if node is None:
            node = self.parse_primary_expression(parse_postfix=False)
        token = self.stream.expect('lparen')
        args = []
        kwargs = []
        dyn_args = None
        dyn_kwargs = None
        require_comma = False

        def ensure(expr):
            if not expr:
                raise TemplateSyntaxError('invalid syntax for function '
                                          'call expression', token.lineno,
                                          self.filename)

        while self.stream.current.type != 'rparen':
            if require_comma:
                self.stream.expect('comma')
                # support for trailing comma
                if self.stream.current.type == 'rparen':
                    break
            if self.stream.current.type == 'mul':
                ensure(dyn_args is None and dyn_kwargs is None)
                self.stream.next()
                dyn_args = self.parse_expression()
            elif self.stream.current.type == 'pow':
                ensure(dyn_kwargs is None)
                self.stream.next()
                dyn_kwargs = self.parse_expression()
            else:
                ensure(dyn_args is None and dyn_kwargs is None)
                if self.stream.current.type == 'name' and \
                    self.stream.look().type == 'assign':
                    key = self.stream.current.value
                    self.stream.skip(2)
                    kwargs.append((key, self.parse_expression()))
                else:
                    ensure(not kwargs)
                    args.append(self.parse_expression())

            require_comma = True
        self.stream.expect('rparen')

        return nodes.CallExpression(node, args, kwargs, dyn_args,
                                    dyn_kwargs, token.lineno,
                                    self.filename)

    def parse_filter_expression(self, node):
        """
        Parse filter calls.
        """
        lineno = self.stream.lineno
        filters = []
        while self.stream.current.type == 'pipe':
            self.stream.next()
            token = self.stream.expect('name')
            args = []
            if self.stream.current.type == 'lparen':
                self.stream.next()
                while self.stream.current.type != 'rparen':
                    if args:
                        self.stream.expect('comma')
                    args.append(self.parse_expression())
                self.stream.expect('rparen')
            filters.append((token.value, args))
        return nodes.FilterExpression(node, filters, lineno, self.filename)

    def parse_test_expression(self, node):
        """
        Parse test calls.
        """
        token = self.stream.expect('is')
        if self.stream.current.type == 'not':
            self.stream.next()
            negated = True
        else:
            negated = False
        name = self.stream.expect('name').value
        args = []
        if self.stream.current.type == 'lparen':
            self.stream.next()
            while self.stream.current.type != 'rparen':
                if args:
                    self.stream.expect('comma')
                args.append(self.parse_expression())
            self.stream.expect('rparen')
        elif self.stream.current.type in ('name', 'string', 'integer',
                                          'float', 'lparen', 'lbracket',
                                          'lbrace', 'regex'):
            args.append(self.parse_expression())
        node = nodes.TestExpression(node, name, args, token.lineno,
                                    self.filename)
        if negated:
            node = nodes.NotExpression(node, token.lineno, self.filename)
        return node

    def test_name(self, name):
        """
        Test if a name is not a special constant
        """
        if name in ('true', 'false', 'none', 'undefined', '_'):
            raise TemplateSyntaxError('expected name not special constant',
                                      self.stream.lineno, self.filename)

    def subparse(self, test, drop_needle=False):
        """
        Helper function used to parse the sourcecode until the test
        function which is passed a tuple in the form (lineno, token, data)
        returns True. In that case the current token is pushed back to
        the stream and the generator ends.

        The test function is only called for the first token after a
        block tag. Variable tags are *not* aliases for {% print %} in
        that case.

        If drop_needle is True the needle_token is removed from the
        stream.
        """
        if self.closed:
            raise RuntimeError('parser is closed')
        result = []
        buffer = []
        next = self.stream.next
        lineno = self.stream.lineno

        def assemble_list():
            push_buffer()
            return nodes.NodeList(result, lineno, self.filename)

        def push_variable():
            buffer.append((True, self.parse_tuple_expression()))

        def push_data():
            buffer.append((False, self.stream.expect('data')))

        def push_buffer():
            if not buffer:
                return
            template = []
            variables = []
            for is_var, data in buffer:
                if is_var:
                    template.append('%s')
                    variables.append(data)
                else:
                    template.append(data.value.replace('%', '%%'))
            result.append(nodes.Text(u''.join(template), variables,
                                     buffer[0][1].lineno, self.filename))
            del buffer[:]

        def push_node(node):
            push_buffer()
            result.append(node)

        while self.stream:
            token_type = self.stream.current.type
            if token_type == 'variable_begin':
                next()
                push_variable()
                self.stream.expect('variable_end')
            elif token_type == 'raw_begin':
                next()
                push_data()
                self.stream.expect('raw_end')
            elif token_type == 'block_begin':
                next()
                if test is not None and test(self.stream.current):
                    if drop_needle:
                        next()
                    return assemble_list()
                handler = self.directives.get(self.stream.current.type)
                if handler is None:
                    if self.no_variable_block:
                        push_variable()
                        self.stream.expect('block_end')
                    elif self.stream.current.type in self.context_directives:
                        raise TemplateSyntaxError('unexpected directive %r.' %
                                                  self.stream.current.type,
                                                  lineno, self.filename)
                    else:
                        name = self.stream.current.value
                        raise TemplateSyntaxError('unknown directive %r.' %
                                                  name, lineno, self.filename)
                else:
                    node = handler()
                    if node is not None:
                        push_node(node)
            elif token_type == 'data':
                push_data()

            # this should be unreachable code
            else:
                assert False, "unexpected token %r" % self.stream.current

        if test is not None:
            msg = isinstance(test, StateTest) and ': ' + test.msg or ''
            raise TemplateSyntaxError('unexpected end of stream' + msg,
                                      self.stream.lineno, self.filename)

        return assemble_list()

    def sanitize_tree(self, body, extends):
        self._sanitize_tree([body], [body], extends, body)
        return body

    def _sanitize_tree(self, nodelist, stack, extends, body):
        """
        This is not a closure because python leaks memory if it is.  It's used
        by `parse()` to make sure blocks do not trigger unexpected behavior.
        """
        for node in nodelist:
            if extends is not None and \
                 node.__class__ is nodes.Block and \
                 stack[-1] is not body:
                for n in stack:
                    if n.__class__ is nodes.Block:
                        break
                else:
                    raise TemplateSyntaxError('misplaced block %r, '
                                              'blocks in child '
                                              'templates must be '
                                              'either top level or '
                                              'located in a block '
                                              'tag.' % node.name,
                                              node.lineno,
                                              self.filename)
            stack.append(node)
            self._sanitize_tree(node.get_child_nodes(), stack, extends, body)
            stack.pop()

    def parse(self):
        """
        Parse the template and return a Template node. This also does some
        post processing sanitizing and parses for an extends tag.
        """
        if self.closed:
            raise RuntimeError('parser is closed')

        try:
            # get the leading whitespace, if we are not in a child
            # template we push that back to the stream later.
            leading_whitespace = self.stream.read_whitespace()

            # parse an optional extends which *must* be the first node
            # of a template.
            if self.stream.current.type == 'block_begin' and \
               self.stream.look().type == 'extends':
                self.stream.skip(2)
                extends = self.stream.expect('string').value
                self.stream.expect('block_end')
            else:
                extends = None
                if leading_whitespace:
                    self.stream.shift(leading_whitespace)

            body = self.sanitize_tree(self.subparse(None), extends)
            return nodes.Template(extends, body, 1, self.filename)
        finally:
            self.close()

    def close(self):
        """Clean up soon."""
        self.closed = True
        self.stream = self.directives = self.stream = self.blocks = \
            self.environment = None
