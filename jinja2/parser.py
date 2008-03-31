# -*- coding: utf-8 -*-
"""
    jinja2.parser
    ~~~~~~~~~~~~~

    Implements the template parser.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import nodes
from jinja2.exceptions import TemplateSyntaxError


__all__ = ['Parser']

_statement_keywords = frozenset(['for', 'if', 'block', 'extends', 'include'])
_compare_operators = frozenset(['eq', 'ne', 'lt', 'lteq', 'gt', 'gteq', 'in'])
_tuple_edge_tokens = set(['rparen', 'block_end', 'variable_end', 'in',
                         'semicolon', 'recursive'])
_statement_end_tokens = set(['elif', 'else', 'endblock', 'endfilter',
                             'endfor', 'endif', 'endmacro',
                             'endcall', 'block_end'])


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
        self.blocks = set()
        self.no_variable_block = self.environment.lexer.no_variable_block
        self.stream = environment.lexer.tokenize(source, filename)

    def end_statement(self):
        """Make sure that the statement ends properly."""
        if self.stream.current.type is 'semicolon':
            self.stream.next()
        elif self.stream.current.type not in _statement_end_tokens:
            raise TemplateSyntaxError('ambigous end of statement',
                                      self.stream.current.lineno,
                                      self.filename)

    def parse_statement(self):
        """Parse a single statement."""
        token_type = self.stream.current.type
        if token_type in _statement_keywords:
            return getattr(self, 'parse_' + token_type)()
        elif token_type is 'call':
            self.stream.next()
            return self.parse_call_block()
        lineno = self.stream.current.lineno
        expr = self.parse_expression()
        if self.stream.current.type == 'assign':
            return self.parse_assign(expr)
        self.end_statement()
        return nodes.ExprStmt(expr, lineno=lineno)

    def parse_assign(self, target):
        """Parse an assign statement."""
        lineno = self.stream.expect('assign').lineno
        if not target.can_assign():
            raise TemplateSyntaxError("can't assign to '%s'" %
                                      target, target.lineno,
                                      self.filename)
        expr = self.parse_tuple()
        self.end_statement()
        nodes.set_ctx(target, 'store')
        return nodes.Assign(target, expr, lineno=lineno)

    def parse_statements(self, end_tokens, drop_needle=False):
        """
        Parse multiple statements into a list until one of the end tokens
        is reached.  This is used to parse the body of statements as it
        also parses template data if appropriate.
        """
        # the first token may be a colon for python compatibility
        if self.stream.current.type is 'colon':
            self.stream.next()

        if self.stream.current.type is 'block_end':
            self.stream.next()
            result = self.subparse(end_tokens)
        else:
            result = []
            while self.stream.current.type not in end_tokens:
                result.append(self.parse_statement())
        if drop_needle:
            self.stream.next()
        return result

    def parse_for(self):
        """Parse a for loop."""
        lineno = self.stream.expect('for').lineno
        target = self.parse_tuple(simplified=True)
        nodes.set_ctx(target, 'store')
        self.stream.expect('in')
        iter = self.parse_tuple()
        if self.stream.current.type is 'recursive':
            self.stream.next()
            recursive = True
        else:
            recursive = False
        body = self.parse_statements(('endfor', 'else'))
        token_type = self.stream.current.type
        self.stream.next()
        if token_type is 'endfor':
            else_ = []
        else:
            else_ = self.parse_statements(('endfor',), drop_needle=True)
        return nodes.For(target, iter, body, else_, False, lineno=lineno)

    def parse_if(self):
        pass

    def parse_block(self):
        pass

    def parse_extends(self):
        pass

    def parse_include(self):
        pass

    def parse_call_block(self):
        pass

    def parse_expression(self):
        """Parse an expression."""
        return self.parse_condexpr()

    def parse_condexpr(self):
        lineno = self.stream.current.lineno
        expr1 = self.parse_or()
        while self.stream.current.type is 'if':
            self.stream.next()
            expr2 = self.parse_or()
            self.stream.expect('else')
            expr3 = self.parse_condexpr()
            expr1 = nodes.CondExpr(expr2, expr1, expr3, lineno=lineno)
            lineno = self.stream.current.lineno
        return expr1

    def parse_or(self):
        lineno = self.stream.current.lineno
        left = self.parse_and()
        while self.stream.current.type is 'or':
            self.stream.next()
            right = self.parse_and()
            left = nodes.Or(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_and(self):
        lineno = self.stream.current.lineno
        left = self.parse_compare()
        while self.stream.current.type is 'and':
            self.stream.next()
            right = self.parse_compare()
            left = nodes.And(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_compare(self):
        lineno = self.stream.current.lineno
        expr = self.parse_add()
        ops = []
        while 1:
            token_type = self.stream.current.type
            if token_type in _compare_operators:
                self.stream.next()
                ops.append(nodes.Operand(token_type, self.parse_add()))
            elif token_type is 'not' and self.stream.look().type is 'in':
                self.stream.skip(2)
                ops.append(nodes.Operand('notin', self.parse_add()))
            else:
                break
            lineno = self.stream.current.lineno
        if not ops:
            return expr
        return nodes.Compare(expr, ops, lineno=lineno)

    def parse_add(self):
        lineno = self.stream.current.lineno
        left = self.parse_sub()
        while self.stream.current.type is 'add':
            self.stream.next()
            right = self.parse_sub()
            left = nodes.Add(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_sub(self):
        lineno = self.stream.current.lineno
        left = self.parse_concat()
        while self.stream.current.type is 'sub':
            self.stream.next()
            right = self.parse_concat()
            left = nodes.Sub(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_concat(self):
        lineno = self.stream.current.lineno
        args = [self.parse_mul()]
        while self.stream.current.type is 'tilde':
            self.stream.next()
            args.append(self.parse_mul())
        if len(args) == 1:
            return args[0]
        return nodes.Concat(args, lineno=lineno)

    def parse_mul(self):
        lineno = self.stream.current.lineno
        left = self.parse_div()
        while self.stream.current.type is 'mul':
            self.stream.next()
            right = self.parse_div()
            left = nodes.Mul(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_div(self):
        lineno = self.stream.current.lineno
        left = self.parse_floordiv()
        while self.stream.current.type is 'div':
            self.stream.next()
            right = self.parse_floordiv()
            left = nodes.Floor(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_floordiv(self):
        lineno = self.stream.current.lineno
        left = self.parse_mod()
        while self.stream.current.type is 'floordiv':
            self.stream.next()
            right = self.parse_mod()
            left = nodes.FloorDiv(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_mod(self):
        lineno = self.stream.current.lineno
        left = self.parse_pow()
        while self.stream.current.type is 'mod':
            self.stream.next()
            right = self.parse_pow()
            left = nodes.Mod(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_pow(self):
        lineno = self.stream.current.lineno
        left = self.parse_unary()
        while self.stream.current.type is 'pow':
            self.stream.next()
            right = self.parse_unary()
            left = nodes.Pow(left, right, lineno=lineno)
            lineno = self.stream.current.lineno
        return left

    def parse_unary(self):
        token_type = self.stream.current.type
        lineno = self.stream.current.lineno
        if token_type is 'not':
            self.stream.next()
            node = self.parse_unary()
            return nodes.Neg(node, lineno=lineno)
        if token_type is 'sub':
            self.stream.next()
            node = self.parse_unary()
            return nodes.Sub(node, lineno=lineno)
        if token_type is 'add':
            self.stream.next()
            node = self.parse_unary()
            return nodes.Pos(node, lineno=lineno)
        return self.parse_primary()

    def parse_primary(self, parse_postfix=True):
        token = self.stream.current
        if token.type is 'name':
            if token.value in ('true', 'false'):
                node = nodes.Const(token.value == 'true', lineno=token.lineno)
            elif token.value == 'none':
                node = nodes.Const(None, lineno=token.lineno)
            else:
                node = nodes.Name(token.value, 'load', lineno=token.lineno)
            self.stream.next()
        elif token.type in ('integer', 'float', 'string'):
            self.stream.next()
            node = nodes.Const(token.value, lineno=token.lineno)
        elif token.type is 'lparen':
            self.stream.next()
            node = self.parse_tuple()
            self.stream.expect('rparen')
        elif token.type is 'lbracket':
            node = self.parse_list()
        elif token.type is 'lbrace':
            node = self.parse_dict()
        else:
            raise TemplateSyntaxError("unexpected token '%s'" %
                                      (token,), token.lineno,
                                      self.filename)
        if parse_postfix:
            node = self.parse_postfix(node)
        return node

    def parse_tuple(self, enforce=False, simplified=False):
        """
        Parse multiple expressions into a tuple. This can also return
        just one expression which is not a tuple. If you want to enforce
        a tuple, pass it enforce=True (currently unused).
        """
        lineno = self.stream.current.lineno
        parse = simplified and self.parse_primary or self.parse_expression
        args = []
        is_tuple = False
        while 1:
            if args:
                self.stream.expect('comma')
            if self.stream.current.type in _tuple_edge_tokens:
                break
            args.append(parse())
            if self.stream.current.type is not 'comma':
                break
            is_tuple = True
            lineno = self.stream.current.lineno
        if not is_tuple and args:
            if enforce:
                raise TemplateSyntaxError('tuple expected', lineno,
                                          self.filename)
            return args[0]
        return nodes.Tuple(args, 'load', lineno=lineno)

    def parse_list(self):
        token = self.stream.expect('lbracket')
        items = []
        while self.stream.current.type is not 'rbracket':
            if items:
                self.stream.expect('comma')
            if self.stream.current.type == 'rbracket':
                break
            items.append(self.parse_expression())
        self.stream.expect('rbracket')
        return nodes.List(items, lineno=token.lineno)

    def parse_dict(self):
        token = self.stream.expect('lbrace')
        items = []
        while self.stream.current.type is not 'rbrace':
            if items:
                self.stream.expect('comma')
            if self.stream.current.type == 'rbrace':
                break
            key = self.parse_expression()
            self.stream.expect('colon')
            value = self.parse_expression()
            items.append(nodes.Pair(key, value, lineno=key.lineno))
        self.stream.expect('rbrace')
        return nodes.Dict(items, token.lineno, self.filename)

    def parse_postfix(self, node):
        while 1:
            token_type = self.stream.current.type
            if token_type is 'dot' or token_type is 'lbracket':
                node = self.parse_subscript(node)
            elif token_type is 'lparen':
                node = self.parse_call(node)
            elif token_type is 'pipe':
                node = self.parse_filter(node)
            elif token_type is 'is':
                node = self.parse_test(node)
            else:
                break
        return node

    def parse_subscript(self, node):
        token = self.stream.next()
        if token.type is 'dot':
            if token.type not in ('name', 'integer'):
                raise TemplateSyntaxError('expected name or number',
                                          token.lineno, self.filename)
            arg = nodes.Const(token.value, lineno=token.lineno)
            self.stream.next()
        elif token.type is 'lbracket':
            args = []
            while self.stream.current.type is not 'rbracket':
                if args:
                    self.stream.expect('comma')
                args.append(self.parse_subscribed())
            self.stream.expect('rbracket')
            if len(args) == 1:
                arg = args[0]
            else:
                arg = nodes.Tuple(args, lineno, self.filename)
        else:
            raise TemplateSyntaxError('expected subscript expression',
                                      self.lineno, self.filename)
        return nodes.Subscript(node, arg, 'load', lineno=token.lineno)

    def parse_subscribed(self):
        lineno = self.stream.current.lineno

        if self.stream.current.type is 'colon':
            self.stream.next()
            args = [None]
        else:
            node = self.parse_expression()
            if self.stream.current.type is not 'colon':
                return node
            self.stream.next()
            args = [node]

        if self.stream.current.type is 'colon':
            args.append(None)
        elif self.stream.current.type not in ('rbracket', 'comma'):
            args.append(self.parse_expression())
        else:
            args.append(None)

        if self.stream.current.type is 'colon':
            self.stream.next()
            if self.stream.current.type not in ('rbracket', 'comma'):
                args.append(self.parse_expression())
            else:
                args.append(None)
        else:
            args.append(None)

        return nodes.Slice(lineno=lineno, *args)

    def parse_call(self, node):
        token = self.stream.expect('lparen')
        args = []
        kwargs = []
        dyn_args = dyn_kwargs = None
        require_comma = False

        def ensure(expr):
            if not expr:
                raise TemplateSyntaxError('invalid syntax for function '
                                          'call expression', token.lineno,
                                          self.filename)

        while self.stream.current.type is not 'rparen':
            if require_comma:
                self.stream.expect('comma')
                # support for trailing comma
                if self.stream.current.type is 'rparen':
                    break
            if self.stream.current.type is 'mul':
                ensure(dyn_args is None and dyn_kwargs is None)
                self.stream.next()
                dyn_args = self.parse_expression()
            elif self.stream.current.type is 'pow':
                ensure(dyn_kwargs is None)
                self.stream.next()
                dyn_kwargs = self.parse_expression()
            else:
                ensure(dyn_args is None and dyn_kwargs is None)
                if self.stream.current.type is 'name' and \
                    self.stream.look().type is 'assign':
                    key = self.stream.current.value
                    self.stream.skip(2)
                    kwargs.append(nodes.Pair(key, self.parse_expression(),
                                             lineno=key.lineno))
                else:
                    ensure(not kwargs)
                    args.append(self.parse_expression())

            require_comma = True
        self.stream.expect('rparen')

        if node is None:
            return args, kwargs, dyn_args, dyn_kwargs
        return nodes.Call(node, args, kwargs, dyn_args, dyn_kwargs,
                          lineno=token.lineno)

    def parse_filter(self, node):
        lineno = self.stream.current.type
        filters = []
        while self.stream.current.type == 'pipe':
            self.stream.next()
            token = self.stream.expect('name')
            if self.stream.current.type is 'lparen':
                args, kwargs, dyn_args, dyn_kwargs = self.parse_call(None)
            else:
                args = []
                kwargs = []
                dyn_args = dyn_kwargs = None
            filters.append(nodes.FilterCall(token.value, args, kwargs,
                                            dyn_args, dyn_kwargs,
                                            lineno=token.lineno))
        return nodes.Filter(node, filters)

    def parse_test(self, node):
        token = self.stream.expect('is')
        if self.stream.current.type is 'not':
            self.stream.next()
            negated = True
        else:
            negated = False
        name = self.stream.expect('name').value
        if self.stream.current.type is 'lparen':
            args, kwargs, dyn_args, dyn_kwargs = self.parse_call(None)
        elif self.stream.current.type in ('name', 'string', 'integer',
                                          'float', 'lparen', 'lbracket',
                                          'lbrace', 'regex'):
            args = [self.parse_expression()]
        else:
            args = []
            kwargs = []
            dyn_args = dyn_kwargs = None
        node = nodes.Test(node, name, args, kwargs, dyn_args,
                          dyn_kwargs, lineno=token.lineno)
        if negated:
            node = nodes.NotExpression(node, lineno=token.lineno)
        return node

    def subparse(self, end_tokens=None):
        body = []
        data_buffer = []
        add_data = data_buffer.append

        def flush_data():
            if data_buffer:
                lineno = data_buffer[0].lineno
                body.append(nodes.Output(data_buffer[:], lineno=lineno))
                del data_buffer[:]

        while self.stream:
            token = self.stream.current
            if token.type is 'data':
                add_data(nodes.Const(token.value, lineno=token.lineno))
                self.stream.next()
            elif token.type is 'variable_begin':
                self.stream.next()
                add_data(self.parse_tuple())
                self.stream.expect('variable_end')
            elif token.type is 'block_begin':
                flush_data()
                self.stream.next()
                if end_tokens is not None and \
                   self.stream.current.type in end_tokens:
                    return body
                while self.stream.current.type is not 'block_end':
                    body.append(self.parse_statement())
                self.stream.expect('block_end')
            else:
                raise AssertionError('internal parsing error')

        flush_data()
        return body

    def parse(self):
        """Parse the whole template into a `Template` node."""
        return nodes.Template(self.subparse(), lineno=1)
