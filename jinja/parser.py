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
from compiler import ast, parse
from jinja import nodes
from jinja.datastructure import StateTest
from jinja.exceptions import TemplateSyntaxError
from jinja.utils import set


__all__ = ['Parser']


# general callback functions for the parser
end_of_block = StateTest.expect_token('block_end', 'end of block tag')
end_of_variable = StateTest.expect_token('variable_end', 'end of variable')
end_of_comment = StateTest.expect_token('comment_end', 'end of comment')

# internal tag callbacks
switch_for = StateTest.expect_name('else', 'endfor')
end_of_for = StateTest.expect_name('endfor')
switch_if = StateTest.expect_name('else', 'elif', 'endif')
end_of_if = StateTest.expect_name('endif')
end_of_filter = StateTest.expect_name('endfilter')
end_of_macro = StateTest.expect_name('endmacro')
end_of_call = StateTest.expect_name('endcall_')
end_of_block_tag = StateTest.expect_name('endblock')
end_of_trans = StateTest.expect_name('endtrans')


class Parser(object):
    """
    The template parser class.

    Transforms sourcecode into an abstract syntax tree.
    """

    def __init__(self, environment, source, filename=None):
        #XXX: with Jinja 1.3 call becomes a keyword. Add it also
        #     to the lexer.py file.
        self.environment = environment
        if isinstance(source, str):
            source = source.decode(environment.template_charset, 'ignore')
        if isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        self.source = source
        self.filename = filename

        #: if this template has a parent template it's stored here
        #: after parsing
        self.extends = None
        #: set for blocks in order to keep them unique
        self.blocks = set()

        #: mapping of directives that require special treatment
        self.directives = {
            'raw':          self.handle_raw_directive,
            'for':          self.handle_for_directive,
            'if':           self.handle_if_directive,
            'cycle':        self.handle_cycle_directive,
            'set':          self.handle_set_directive,
            'filter':       self.handle_filter_directive,
            'print':        self.handle_print_directive,
            'macro':        self.handle_macro_directive,
            'call_':        self.handle_call_directive,
            'block':        self.handle_block_directive,
            'extends':      self.handle_extends_directive,
            'include':      self.handle_include_directive,
            'trans':        self.handle_trans_directive
        }

        #: set of directives that are only available in a certain
        #: context.
        self.context_directives = set([
            'elif', 'else', 'endblock', 'endfilter', 'endfor', 'endif',
            'endmacro', 'endraw', 'endtrans', 'pluralize'
        ])

        #: get the `no_variable_block` flag
        self.no_variable_block = self.environment.lexer.no_variable_block

        self.tokenstream = environment.lexer.tokenize(source, filename)

    def handle_raw_directive(self, lineno, gen):
        """
        Handle fake raw directive. (real raw directives are handled by
        the lexer. But if there are arguments to raw or the end tag
        is missing the parser tries to resolve this directive. In that
        case present the user a useful error message.
        """
        args = list(gen)
        if args:
            raise TemplateSyntaxError('raw directive does not support '
                                      'any arguments.', lineno,
                                      self.filename)
        raise TemplateSyntaxError('missing end tag for raw directive.',
                                  lineno, self.filename)

    def handle_for_directive(self, lineno, gen):
        """
        Handle a for directive and return a ForLoop node
        """
        recursive = []
        def wrapgen():
            """Wrap the generator to check if we have a recursive for loop."""
            for token in gen:
                if token[1:] == ('name', 'recursive'):
                    try:
                        item = gen.next()
                    except StopIteration:
                        recursive.append(True)
                        return
                    yield token
                    yield item
                else:
                    yield token
        ast = self.parse_python(lineno, wrapgen(), 'for %s:pass')
        body = self.subparse(switch_for)

        # do we have an else section?
        if self.tokenstream.next()[2] == 'else':
            self.close_remaining_block()
            else_ = self.subparse(end_of_for, True)
        else:
            else_ = None
        self.close_remaining_block()

        return nodes.ForLoop(lineno, ast.assign, ast.list, body, else_,
                             bool(recursive))

    def handle_if_directive(self, lineno, gen):
        """
        Handle if/else blocks.
        """
        ast = self.parse_python(lineno, gen, 'if %s:pass')
        tests = [(ast.tests[0][0], self.subparse(switch_if))]

        # do we have an else section?
        while True:
            lineno, token, needle = self.tokenstream.next()
            if needle == 'else':
                self.close_remaining_block()
                else_ = self.subparse(end_of_if, True)
                break
            elif needle == 'elif':
                gen = self.tokenstream.fetch_until(end_of_block, True)
                ast = self.parse_python(lineno, gen, 'if %s:pass')
                tests.append((ast.tests[0][0], self.subparse(switch_if)))
            else:
                else_ = None
                break
        self.close_remaining_block()

        return nodes.IfCondition(lineno, tests, else_)

    def handle_cycle_directive(self, lineno, gen):
        """
        Handle {% cycle foo, bar, baz %}.
        """
        ast = self.parse_python(lineno, gen, '_cycle((%s))')
        # ast is something like Discard(CallFunc(Name('_cycle'), ...))
        # skip that.
        return nodes.Cycle(lineno, ast.expr.args[0])

    def handle_set_directive(self, lineno, gen):
        """
        Handle {% set foo = 'value of foo' %}.
        """
        try:
            name = gen.next()
            if name[1] != 'name' or gen.next()[1:] != ('operator', '='):
                raise ValueError()
        except (StopIteration, ValueError):
            raise TemplateSyntaxError('invalid syntax for set', lineno,
                                      self.filename)
        ast = self.parse_python(lineno, gen, '(%s)')
        # disallow keywords
        if not name[2].endswith('_'):
            raise TemplateSyntaxError('illegal use of keyword %r '
                                      'as identifier in set statement.' %
                                      name[2], lineno, self.filename)
        return nodes.Set(lineno, str(name[2][:-1]), ast.expr)

    def handle_filter_directive(self, lineno, gen):
        """
        Handle {% filter foo|bar %} directives.
        """
        ast = self.parse_python(lineno, gen, '_filter(dummy|%s)')
        body = self.subparse(end_of_filter, True)
        self.close_remaining_block()
        return nodes.Filter(lineno, body, ast.expr.args[0].nodes[1:])

    def handle_print_directive(self, lineno, gen):
        """
        Handle {{ foo }} and {% print foo %}.
        """
        ast = self.parse_python(lineno, gen, 'print_(%s)')
        # ast is something like Discard(CallFunc(Name('print_'), ...))
        # so just use the args
        arguments = ast.expr.args
        # we only accept one argument
        if len(arguments) != 1:
            raise TemplateSyntaxError('invalid argument count for print; '
                                      'print requires exactly one argument, '
                                      'got %d.' % len(arguments), lineno,
                                      self.filename)
        return nodes.Print(lineno, arguments[0])

    def handle_macro_directive(self, lineno, gen):
        """
        Handle {% macro foo bar, baz %} as well as
        {% macro foo(bar, baz) %}.
        """
        try:
            macro_name = gen.next()
        except StopIteration:
            raise TemplateSyntaxError('macro requires a name', lineno,
                                      self.filename)
        if macro_name[1] != 'name':
            raise TemplateSyntaxError('expected \'name\', got %r' %
                                      macro_name[1], lineno,
                                      self.filename)
        # disallow keywords as identifiers
        elif not macro_name[2].endswith('_'):
            raise TemplateSyntaxError('illegal use of keyword %r '
                                      'as macro name.' % macro_name[2],
                                      lineno, self.filename)

        # make the punctuation around arguments optional
        arg_list = list(gen)
        if arg_list and arg_list[0][1:] == ('operator', '(') and \
                        arg_list[-1][1:] == ('operator', ')'):
            arg_list = arg_list[1:-1]

        ast = self.parse_python(lineno, arg_list, 'def %s(%%s):pass' %
                                str(macro_name[2][:-1]))
        body = self.subparse(end_of_macro, True)
        self.close_remaining_block()

        if ast.varargs or ast.kwargs:
            raise TemplateSyntaxError('variable length macro signature '
                                      'not allowed.', lineno,
                                      self.filename)
        if ast.argnames:
            defaults = [None] * (len(ast.argnames) - len(ast.defaults)) + \
                       ast.defaults
            args = []
            for idx, argname in enumerate(ast.argnames):
                # disallow keywords as argument names
                if not argname.endswith('_'):
                    raise TemplateSyntaxError('illegal use of keyword %r '
                                              'as macro argument.' % argname,
                                              lineno, self.filename)
                args.append((argname[:-1], defaults[idx]))
        else:
            args = None
        return nodes.Macro(lineno, ast.name, args, body)

    def handle_call_directive(self, lineno, gen):
        """
        Handle {% call foo() %}...{% endcall %}
        """
        expr = self.parse_python(lineno, gen, '(%s)').expr
        if expr.__class__ is not ast.CallFunc:
            raise TemplateSyntaxError('call requires a function or macro '
                                      'call as only argument.', lineno,
                                      self.filename)
        body = self.subparse(end_of_call, True)
        self.close_remaining_block()
        return nodes.Call(lineno, expr, body)

    def handle_block_directive(self, lineno, gen):
        """
        Handle block directives used for inheritance.
        """
        tokens = list(gen)
        if not tokens:
            raise TemplateSyntaxError('block requires a name', lineno,
                                      self.filename)
        block_name = tokens.pop(0)
        if block_name[1] != 'name':
            raise TemplateSyntaxError('expected \'name\', got %r' %
                                      block_name[1], lineno, self.filename)
        # disallow keywords
        if not block_name[2].endswith('_'):
            raise TemplateSyntaxError('illegal use of keyword %r '
                                      'as block name.' % block_name[2],
                                      lineno, self.filename)
        name = block_name[2][:-1]
        # check if this block does not exist by now.
        if name in self.blocks:
            raise TemplateSyntaxError('block %r defined twice' %
                                       name, lineno, self.filename)
        self.blocks.add(name)

        if tokens:
            body = nodes.NodeList(lineno, [nodes.Print(lineno,
                   self.parse_python(lineno, tokens, '(%s)').expr)])
        else:
            # otherwise parse the body and attach it to the block
            body = self.subparse(end_of_block_tag, True)
            self.close_remaining_block()
        return nodes.Block(lineno, name, body)

    def handle_extends_directive(self, lineno, gen):
        """
        Handle the extends directive used for inheritance.
        """
        tokens = list(gen)
        if len(tokens) != 1 or tokens[0][1] != 'string':
            raise TemplateSyntaxError('extends requires a string', lineno,
                                      self.filename)
        if self.extends is not None:
            raise TemplateSyntaxError('extends called twice', lineno,
                                      self.filename)
        self.extends = nodes.Extends(lineno, tokens[0][2][1:-1])

    def handle_include_directive(self, lineno, gen):
        """
        Handle the include directive used for template inclusion.
        """
        tokens = list(gen)
        # hardcoded include (faster because copied into the bytecode)
        if len(tokens) == 1 and tokens[0][1] == 'string':
            return nodes.Include(lineno, str(tokens[0][2][1:-1]))
        raise TemplateSyntaxError('invalid syntax for include '
                                  'directive. Requires a hardcoded '
                                  'string', lineno,
                                  self.filename)

    def handle_trans_directive(self, lineno, gen):
        """
        Handle translatable sections.
        """
        def process_variable(lineno, token, name):
            if token != 'name':
                raise TemplateSyntaxError('can only use variable not '
                                          'constants or expressions in '
                                          'translation variable blocks.',
                                          lineno, self.filename)
            # plural name without trailing "_"? that's a keyword
            if not name.endswith('_'):
                raise TemplateSyntaxError('illegal use of keyword \'%s\' as '
                                          'identifier in translatable block.'
                                          % name, lineno, self.filename)
            name = name[:-1]
            if name not in replacements:
                raise TemplateSyntaxError('unregistered translation variable'
                                          " '%s'." % name, lineno,
                                          self.filename)
            # check that we don't have an expression here, thus the
            # next token *must* be a variable_end token (or a
            # block_end token when in no_variable_block mode)
            next_token = self.tokenstream.next()[1]
            if next_token != 'variable_end' and not \
               (self.no_variable_block and next_token == 'block_end'):
                raise TemplateSyntaxError('you cannot use variable '
                                          'expressions inside translatable '
                                          'tags. apply filters in the '
                                          'trans header.', lineno,
                                          self.filename)
            buf.append('%%(%s)s' % name)

        # save the initial line number for the resulting node
        flineno = lineno
        try:
            # check for string translations
            try:
                lineno, token, data = gen.next()
            except StopIteration:
                # no dynamic replacements
                replacements = {}
                first_var = None
            else:
                if token == 'string':
                    # check that there are not any more elements
                    try:
                        gen.next()
                    except StopIteration:
                        # XXX: this looks fishy
                        data = data[1:-1].encode('utf-8').decode('string-escape')
                        return nodes.Trans(lineno, data.decode('utf-8'), None,
                                           None, None)
                    raise TemplateSyntaxError('string based translations '
                                              'require at most one argument.',
                                              lineno, self.filename)
                # create a new generator with the popped item as first one
                def wrapgen(oldgen):
                    yield lineno, token, data
                    for item in oldgen:
                        yield item
                gen = wrapgen(gen)

                # block based translations
                first_var = None
                replacements = {}
                for arg in self.parse_python(lineno, gen,
                                             '_trans(%s)').expr.args:
                    if arg.__class__ not in (ast.Keyword, ast.Name):
                        raise TemplateSyntaxError('translation tags need expl'
                                                  'icit names for values.',
                                                  lineno, self.filename)
                    # disallow keywords
                    if not arg.name.endswith('_'):
                        raise TemplateSyntaxError("illegal use of keyword '%s"
                                                  '\' as identifier.' %
                                                  arg.name, lineno,
                                                  self.filename)
                    # remove the last "_" before writing
                    name = arg.name[:-1]
                    if first_var is None:
                        first_var = name
                    # if it's a keyword use the expression as value,
                    # otherwise just reuse the name node.
                    replacements[name] = getattr(arg, 'expr', arg)

            # look for endtrans/pluralize
            buf = singular = []
            plural = indicator = None

            while True:
                lineno, token, data = self.tokenstream.next()
                # comments
                if token == 'comment_begin':
                    self.tokenstream.drop_until(end_of_comment, True)
                # nested variables
                elif token == 'variable_begin':
                    process_variable(*self.tokenstream.next())
                # nested blocks are not supported, just look for end blocks
                elif token == 'block_begin':
                    _, block_token, block_name = self.tokenstream.next()
                    if block_token != 'name' or \
                       block_name not in ('pluralize', 'endtrans'):
                        # if we have a block name check if it's a real
                        # directive or a not existing one (which probably
                        # is a typo)
                        if block_token == 'name':
                            # if this block is a context directive the
                            # designer has probably misspelled endtrans
                            # with endfor or something like that. raise
                            # a nicer error message
                            if block_name in self.context_directives:
                                raise TemplateSyntaxError('unexpected directi'
                                                          "ve '%s' found" %
                                                          block_name, lineno,
                                                          self.filename)
                            # if's not a directive, probably misspelled
                            # endtrans. Raise the "unknown directive"
                            # exception rather than the "not allowed"
                            if block_name not in self.directives:
                                if block_name.endswith('_'):
                                    # if we don't have a variable block we
                                    # have to process this as variable.
                                    if self.no_variable_block:
                                        process_variable(_, block_token,
                                                         block_name)
                                        continue
                                    block_name = block_name[:-1]
                                raise TemplateSyntaxError('unknown directive'
                                                          " '%s'" % block_name,
                                                          lineno,
                                                          self.filename)
                        # we have something different and are in the
                        # special no_variable_block mode. process this
                        # as variable
                        elif self.no_variable_block:
                            process_variable(_, block_token, block_name)
                            continue
                        # if it's indeed a known directive we better
                        # raise an exception informing the user about
                        # the fact that we don't support blocks in
                        # translatable sections.
                        raise TemplateSyntaxError('directives in translatable'
                                                  ' sections are not '
                                                  'allowed', lineno,
                                                  self.filename)
                    # pluralize
                    if block_name == 'pluralize':
                        if plural is not None:
                            raise TemplateSyntaxError('translation blocks '
                                                      'support at most one '
                                                      'plural block',
                                                      lineno, self.filename)
                        _, plural_token, plural_name = self.tokenstream.next()
                        if plural_token == 'block_end':
                            indicator = first_var
                        elif plural_token == 'name':
                            # disallow keywords
                            if not plural_name.endswith('_'):
                                raise TemplateSyntaxError('illegal use of '
                                                          "keyword '%s' as "
                                                          'identifier.' %
                                                          plural_name,
                                                          lineno,
                                                          self.filename)
                            plural_name = plural_name[:-1]
                            if plural_name not in replacements:
                                raise TemplateSyntaxError('unregistered '
                                                          'translation '
                                                          "variable '%s'" %
                                                          plural_name, lineno,
                                                          self.filename)
                            elif self.tokenstream.next()[1] != 'block_end':
                                raise TemplateSyntaxError('pluralize takes '
                                                          'at most one '
                                                          'argument', lineno,
                                                          self.filename)
                            indicator = plural_name
                        else:
                            raise TemplateSyntaxError('pluralize requires no '
                                                      'argument or a variable'
                                                      ' name.', lineno,
                                                      self.filename)
                        plural = buf = []
                    # end translation
                    elif block_name == 'endtrans':
                        self.close_remaining_block()
                        break
                # normal data
                else:
                    buf.append(data.replace('%', '%%'))

        except StopIteration:
            raise TemplateSyntaxError('unexpected end of translation section',
                                      self.tokenstream.last[0], self.filename)

        singular = u''.join(singular)
        if plural is not None:
            plural = u''.join(plural)
        return nodes.Trans(flineno, singular, plural, indicator,
                           replacements or None)

    def parse_python(self, lineno, gen, template):
        """
        Convert the passed generator into a flat string representing
        python sourcecode and return an ast node or raise a
        TemplateSyntaxError.
        """
        tokens = []
        for t_lineno, t_token, t_data in gen:
            if t_token == 'string':
                # because some libraries have problems with unicode
                # objects we do some lazy unicode processing here.
                # if a string is ASCII only we yield it as string
                # in other cases as unicode. This works around
                # problems with datetimeobj.strftime()
                # also escape newlines in strings
                t_data = t_data.replace('\n', '\\n')
                try:
                    str(t_data)
                except UnicodeError:
                    tokens.append('u' + t_data)
                    continue
            tokens.append(t_data)
        source = '\xef\xbb\xbf' + (template % (u' '.join(tokens)).
                                   encode('utf-8'))
        try:
            ast = parse(source, 'exec')
        except SyntaxError, e:
            raise TemplateSyntaxError('invalid syntax in expression',
                                      lineno + (e.lineno or 0),
                                      self.filename)
        assert len(ast.node.nodes) == 1, 'get %d nodes, 1 expected' % \
                                         len(ast.node.nodes)
        result = ast.node.nodes[0]
        nodes.inc_lineno(lineno, result)
        return result

    def parse(self):
        """
        Parse the template and return a Template node. Also unescape the
        names escaped by the lexer (unused python keywords) and set the
        filename attributes for all nodes in the tree.
        """
        body = self.subparse(None)
        def walk(nodes_, stack):
            for node in nodes_:
                # all names excluding keywords have an trailing underline.
                # if we find a name without trailing underline that's a
                # keyword and this code raises an error. else strip the
                # underline again
                if node.__class__ in (ast.AssName, ast.Name, ast.Keyword):
                    if not node.name.endswith('_'):
                        raise TemplateSyntaxError('illegal use of keyword %r '
                                                  'as identifier.' %
                                                  node.name, node.lineno,
                                                  self.filename)
                    node.name = node.name[:-1]
                # same for attributes
                elif node.__class__ is ast.Getattr:
                    if not node.attrname.endswith('_'):
                        raise TemplateSyntaxError('illegal use of keyword %r '
                                                  'as attribute name.' %
                                                  node.name, node.lineno,
                                                  self.filename)
                    node.attrname = node.attrname[:-1]
                # if we have a ForLoop we ensure that nobody patches existing
                # object using "for foo.bar in seq"
                elif node.__class__ is nodes.ForLoop:
                    def check(node):
                        if node.__class__ not in (ast.AssName, ast.AssTuple):
                            raise TemplateSyntaxError('can\'t assign to '
                                                      'expression.',
                                                      node.lineno,
                                                      self.filename)
                        for n in node.getChildNodes():
                            check(n)
                    check(node.item)
                # ensure that in child templates block are either top level
                # or located inside of another block tag.
                elif self.extends is not None and \
                     node.__class__ is nodes.Block:
                    if stack[-1] is not body:
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
                # now set the filename and continue working on the childnodes
                node.filename = self.filename
                stack.append(node)
                walk(node.getChildNodes(), stack)
                stack.pop()
        walk([body], [body])
        return nodes.Template(self.filename, body, self.extends)

    def subparse(self, test, drop_needle=False):
        """
        Helper function used to parse the sourcecode until the test
        function which is passed a tuple in the form (lineno, token, data)
        returns True. In that case the current token is pushed back to
        the tokenstream and the generator ends.

        The test function is only called for the first token after a
        block tag. Variable tags are *not* aliases for {% print %} in
        that case.

        If drop_needle is True the needle_token is removed from the
        tokenstream.
        """
        def finish():
            """Helper function to remove unused nodelists."""
            if data_buffer:
                flush_data_buffer()
            if len(result) == 1:
                return result[0]
            return result

        def flush_data_buffer():
            """Helper function to write the contents of the buffer
            to the result nodelist."""
            format_string = []
            insertions = []
            for item in data_buffer:
                if item[0] == 'variable':
                    p = self.handle_print_directive(*item[1:])
                    format_string.append('%s')
                    insertions.append(p)
                else:
                    format_string.append(item[2].replace('%', '%%'))
            # if we do not have insertions yield it as text node
            if not insertions:
                result.append(nodes.Text(data_buffer[0][1],
                              (u''.join(format_string)).replace('%%', '%')))
            # if we do not have any text data we yield some variable nodes
            elif len(insertions) == len(format_string):
                result.extend(insertions)
            # otherwise we go with a dynamic text node
            else:
                result.append(nodes.DynamicText(data_buffer[0][1],
                                                u''.join(format_string),
                                                insertions))
            # clear the buffer
            del data_buffer[:]

        def process_variable(gen):
            data_buffer.append(('variable', lineno, tuple(gen)))

        lineno = self.tokenstream.last[0]
        result = nodes.NodeList(lineno)
        data_buffer = []
        for lineno, token, data in self.tokenstream:
            # comments
            if token == 'comment_begin':
                self.tokenstream.drop_until(end_of_comment, True)

            # this token marks the begin or a variable section.
            # parse everything till the end of it.
            elif token == 'variable_begin':
                gen = self.tokenstream.fetch_until(end_of_variable, True)
                process_variable(gen)

            # this token marks the start of a block. like for variables
            # just parse everything until the end of the block
            elif token == 'block_begin':
                # if we have something in the buffer we write the
                # data back
                if data_buffer:
                    flush_data_buffer()

                node = None
                gen = self.tokenstream.fetch_until(end_of_block, True)
                try:
                    lineno, token, data = gen.next()
                except StopIteration:
                    raise TemplateSyntaxError('unexpected end of block',
                                              lineno, self.filename)

                # first token *must* be a name token
                if token != 'name':
                    # well, not always. if we have a lexer without variable
                    # blocks configured we process these tokens as variable
                    # block.
                    if self.no_variable_block:
                        process_variable([(lineno, token, data)] + list(gen))
                    else:
                        raise TemplateSyntaxError('unexpected %r token (%r)' %
                                                  (token, data), lineno,
                                                  self.filename)

                # if a test function is passed to subparse we check if we
                # reached the end of such a requested block.
                if test is not None and test(lineno, token, data):
                    if not drop_needle:
                        self.tokenstream.push(lineno, token, data)
                    return finish()

                # the first token tells us which directive we want to call.
                # if if doesn't match any existing directive it's like a
                # template syntax error.
                if data in self.directives:
                    node = self.directives[data](lineno, gen)
                # context depending directive found
                elif data in self.context_directives:
                    raise TemplateSyntaxError('unexpected directive %r' %
                                              str(data), lineno,
                                              self.filename)
                # keyword or unknown name with trailing slash
                else:
                    # non name token in no_variable_block mode.
                    if token != 'name' and self.no_variable_block:
                        process_variable([(lineno, token, data)] +
                                             list(gen))
                        continue
                    if data.endswith('_'):
                        # it was a non keyword identifier and we have
                        # no variable tag. sounds like we should process
                        # this as variable tag
                        if self.no_variable_block:
                            process_variable([(lineno, token, data)] +
                                             list(gen))
                            continue
                        # otherwise strip the trailing underscore for the
                        # exception that is raised
                        data = data[:-1]
                    raise TemplateSyntaxError('unknown directive %r' %
                                              str(data), lineno,
                                              self.filename)
                # some tags like the extends tag do not output nodes.
                # so just skip that.
                if node is not None:
                    result.append(node)

            # here the only token we should get is "data". all other
            # tokens just exist in block or variable sections. (if the
            # tokenizer is not brocken)
            elif token in 'data':
                data_buffer.append(('text', lineno, data))

            # so this should be unreachable code
            else:
                raise AssertionError('unexpected token %r (%r)' % (token,
                                                                   data))

        # still here and a test function is provided? raise and error
        if test is not None:
            # if the callback is a state test lambda wrapper we
            # can use the `error_message` property to get the error
            if isinstance(test, StateTest):
                msg = ': ' + test.error_message
            else:
                msg = ''
            raise TemplateSyntaxError('unexpected end of template' + msg,
                                      lineno, self.filename)
        return finish()

    def close_remaining_block(self):
        """
        If we opened a block tag because one of our tags requires an end
        tag we can use this method to drop the rest of the block from
        the stream. If the next token isn't the block end we throw an
        error.
        """
        lineno, _, tagname = self.tokenstream.last
        try:
            lineno, token, data = self.tokenstream.next()
        except StopIteration:
            raise TemplateSyntaxError('missing closing tag', lineno,
                                      self.filename)
        if token != 'block_end':
            print token, data, list(self.tokenstream)
            raise TemplateSyntaxError('expected empty %s-directive but '
                                      'found additional arguments.' %
                                      tagname, lineno, self.filename)
