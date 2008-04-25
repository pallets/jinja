# -*- coding: utf-8 -*-
"""
    jinja2.lexer
    ~~~~~~~~~~~~

    This module implements a Jinja / Python combination lexer. The
    `Lexer` class provided by this module is used to do some preprocessing
    for Jinja.

    On the one hand it filters out invalid operators like the bitshift
    operators we don't allow in templates. On the other hand it separates
    template code and python code in expressions.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
import unicodedata
from jinja2.datastructure import TokenStream, Token
from jinja2.exceptions import TemplateSyntaxError
from jinja2.utils import LRUCache


# cache for the lexers. Exists in order to be able to have multiple
# environments with the same lexer
_lexer_cache = LRUCache(10)

# static regular expressions
whitespace_re = re.compile(r'\s+(?um)')
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")(?ms)')
integer_re = re.compile(r'\d+')
name_re = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
float_re = re.compile(r'\d+\.\d+')

# set of used keywords
keywords = set(['and', 'block', 'elif', 'else', 'endblock', 'print',
                'endfilter', 'endfor', 'endif', 'endmacro', 'endraw',
                'extends', 'filter', 'for', 'if', 'in', 'include',
                'is', 'macro', 'not', 'or', 'raw', 'call', 'endcall',
                'from', 'import'])

# bind operators to token types
operators = {
    '+':            'add',
    '-':            'sub',
    '/':            'div',
    '//':           'floordiv',
    '*':            'mul',
    '%':            'mod',
    '**':           'pow',
    '~':            'tilde',
    '[':            'lbracket',
    ']':            'rbracket',
    '(':            'lparen',
    ')':            'rparen',
    '{':            'lbrace',
    '}':            'rbrace',
    '==':           'eq',
    '!=':           'ne',
    '>':            'gt',
    '>=':           'gteq',
    '<':            'lt',
    '<=':           'lteq',
    '=':            'assign',
    '.':            'dot',
    ':':            'colon',
    '|':            'pipe',
    ',':            'comma',
    ';':            'semicolon'
}

reverse_operators = dict([(v, k) for k, v in operators.iteritems()])
assert len(operators) == len(reverse_operators), 'operators dropped'
operator_re = re.compile('(%s)' % '|'.join(re.escape(x) for x in
                         sorted(operators, key=lambda x: -len(x))))

simple_escapes = {
    'a':    '\a',
    'n':    '\n',
    'r':    '\r',
    'f':    '\f',
    't':    '\t',
    'v':    '\v',
    '\\':   '\\',
    '"':    '"',
    "'":    "'",
    '0':    '\x00'
}
unicode_escapes = {
    'x':    2,
    'u':    4,
    'U':    8
}


def unescape_string(lineno, filename, s):
    r"""Unescape a string. Supported escapes:
        \a, \n, \r\, \f, \v, \\, \", \', \0

        \x00, \u0000, \U00000000, \N{...}
    """
    try:
        return s.encode('ascii', 'backslashreplace').decode('unicode-escape')
    except UnicodeError, e:
        msg = str(e).split(':')[-1].strip()
        raise TemplateSyntaxError(msg, lineno, filename)


class Failure(object):
    """Class that raises a `TemplateSyntaxError` if called.
    Used by the `Lexer` to specify known errors.
    """

    def __init__(self, message, cls=TemplateSyntaxError):
        self.message = message
        self.error_class = cls

    def __call__(self, lineno, filename):
        raise self.error_class(self.message, lineno, filename)


class LexerMeta(type):
    """Metaclass for the lexer that caches instances for
    the same configuration in a weak value dictionary.
    """

    def __call__(cls, environment):
        key = (environment.block_start_string,
               environment.block_end_string,
               environment.variable_start_string,
               environment.variable_end_string,
               environment.comment_start_string,
               environment.comment_end_string,
               environment.line_statement_prefix,
               environment.trim_blocks)
        lexer = _lexer_cache.get(key)
        if lexer is None:
            lexer = type.__call__(cls, environment)
            _lexer_cache[key] = lexer
        return lexer


class Lexer(object):
    """Class that implements a lexer for a given environment. Automatically
    created by the environment class, usually you don't have to do that.

    Note that the lexer is not automatically bound to an environment.
    Multiple environments can share the same lexer.
    """

    __metaclass__ = LexerMeta

    def __init__(self, environment):
        # shortcuts
        c = lambda x: re.compile(x, re.M | re.S)
        e = re.escape

        # lexing rules for tags
        tag_rules = [
            (whitespace_re, None, None),
            (float_re, 'float', None),
            (integer_re, 'integer', None),
            (c(r'\b(?:%s)\b' % '|'.join(sorted(keywords, key=lambda x: -len(x)))),
             'keyword', None),
            (name_re, 'name', None),
            (string_re, 'string', None),
            (operator_re, 'operator', None)
        ]

        # assamble the root lexing rule. because "|" is ungreedy
        # we have to sort by length so that the lexer continues working
        # as expected when we have parsing rules like <% for block and
        # <%= for variables. (if someone wants asp like syntax)
        # variables are just part of the rules if variable processing
        # is required.
        root_tag_rules = [
            ('comment',     environment.comment_start_string),
            ('block',       environment.block_start_string),
            ('variable',    environment.variable_start_string)
        ]
        root_tag_rules.sort(key=lambda x: -len(x[1]))

        # now escape the rules.  This is done here so that the escape
        # signs don't count for the lengths of the tags.
        root_tag_rules = [(a, e(b)) for a, b in root_tag_rules]

        # if we have a line statement prefix we need an extra rule for
        # that.  We add this rule *after* all the others.
        if environment.line_statement_prefix is not None:
            prefix = e(environment.line_statement_prefix)
            root_tag_rules.insert(0, ('linestatement', '^\s*' + prefix))

        # block suffix if trimming is enabled
        block_suffix_re = environment.trim_blocks and '\\n?' or ''

        # global lexing rules
        self.rules = {
            'root': [
                # directives
                (c('(.*?)(?:%s)' % '|'.join(
                    ['(?P<raw_begin>(?:\s*%s\-|%s)\s*raw\s*%s)' % (
                        e(environment.block_start_string),
                        e(environment.block_start_string),
                        e(environment.block_end_string)
                    )] + [
                        '(?P<%s_begin>\s*%s\-|%s)' % (n, r, r)
                        for n, r in root_tag_rules
                    ])), ('data', '#bygroup'), '#bygroup'),
                # data
                (c('.+'), 'data', None)
            ],
            # comments
            'comment_begin': [
                (c(r'(.*?)((?:\-%s\s*|%s)%s)' % (
                    e(environment.comment_end_string),
                    e(environment.comment_end_string),
                    block_suffix_re
                )), ('comment', 'comment_end'), '#pop'),
                (c('(.)'), (Failure('Missing end of comment tag'),), None)
            ],
            # blocks
            'block_begin': [
                (c('(?:\-%s\s*|%s)%s' % (
                    e(environment.block_end_string),
                    e(environment.block_end_string),
                    block_suffix_re
                )), 'block_end', '#pop'),
            ] + tag_rules,
            # variables
            'variable_begin': [
                (c('\-%s\s*|%s' % (
                    e(environment.variable_end_string),
                    e(environment.variable_end_string)
                )), 'variable_end', '#pop')
            ] + tag_rules,
            # raw block
            'raw_begin': [
                (c('(.*?)((?:\s*%s\-|%s)\s*endraw\s*(?:\-%s\s*|%s%s))' % (
                    e(environment.block_start_string),
                    e(environment.block_start_string),
                    e(environment.block_end_string),
                    e(environment.block_end_string),
                    block_suffix_re
                )), ('data', 'raw_end'), '#pop'),
                (c('(.)'), (Failure('Missing end of raw directive'),), None)
            ],
            # line statements
            'linestatement_begin': [
                (c(r'\s*(\n|$)'), 'linestatement_end', '#pop')
            ] + tag_rules
        }

    def tokenize(self, source, filename=None):
        """Works like `tokeniter` but returns a tokenstream of tokens and not
        a generator or token tuples.  Additionally all token values are already
        converted into types and postprocessed. For example keywords are
        already keyword tokens, not named tokens, comments are removed,
        integers and floats converted, strings unescaped etc.
        """
        source = unicode(source)
        def generate():
            for lineno, token, value in self.tokeniter(source, filename):
                if token in ('comment_begin', 'comment', 'comment_end'):
                    continue
                elif token == 'linestatement_begin':
                    token = 'block_begin'
                elif token == 'linestatement_end':
                    token = 'block_end'
                # we are not interested in those tokens in the parser
                elif token in ('raw_begin', 'raw_end'):
                    continue
                elif token == 'data':
                    try:
                        value = str(value)
                    except UnicodeError:
                        pass
                elif token == 'keyword':
                    token = value
                elif token == 'name':
                    value = str(value)
                elif token == 'string':
                    value = unescape_string(lineno, filename, value[1:-1])
                    try:
                        value = str(value)
                    except UnicodeError:
                        pass
                elif token == 'integer':
                    value = int(value)
                elif token == 'float':
                    value = float(value)
                elif token == 'operator':
                    token = operators[value]
                yield Token(lineno, token, value)
        return TokenStream(generate(), filename)

    def tokeniter(self, source, filename=None):
        """This method tokenizes the text and returns the tokens in a
        generator.  Use this method if you just want to tokenize a template.
        The output you get is not compatible with the input the jinja parser
        wants.  The parser uses the `tokenize` function with returns a
        `TokenStream` and postprocessed tokens.
        """
        source = '\n'.join(source.splitlines())
        pos = 0
        lineno = 1
        stack = ['root']
        statetokens = self.rules['root']
        source_length = len(source)

        balancing_stack = []

        while 1:
            # tokenizer loop
            for regex, tokens, new_state in statetokens:
                m = regex.match(source, pos)
                # if no match we try again with the next rule
                if m is None:
                    continue

                # we only match blocks and variables if brances / parentheses
                # are balanced. continue parsing with the lower rule which
                # is the operator rule. do this only if the end tags look
                # like operators
                if balancing_stack and \
                   tokens in ('variable_end', 'block_end',
                              'linestatement_end'):
                    continue

                # tuples support more options
                if isinstance(tokens, tuple):
                    for idx, token in enumerate(tokens):
                        # hidden group
                        if token is None:
                            g = m.group(idx)
                            if g:
                                lineno += g.count('\n')
                            continue
                        # failure group
                        elif token.__class__ is Failure:
                            raise token(lineno, filename)
                        # bygroup is a bit more complex, in that case we
                        # yield for the current token the first named
                        # group that matched
                        elif token == '#bygroup':
                            for key, value in m.groupdict().iteritems():
                                if value is not None:
                                    yield lineno, key, value
                                    lineno += value.count('\n')
                                    break
                            else:
                                raise RuntimeError('%r wanted to resolve '
                                                   'the token dynamically'
                                                   ' but no group matched'
                                                   % regex)
                        # normal group
                        else:
                            data = m.group(idx + 1)
                            if data:
                                yield lineno, token, data
                            lineno += data.count('\n')

                # strings as token just are yielded as it.
                else:
                    data = m.group()
                    # update brace/parentheses balance
                    if tokens == 'operator':
                        if data == '{':
                            balancing_stack.append('}')
                        elif data == '(':
                            balancing_stack.append(')')
                        elif data == '[':
                            balancing_stack.append(']')
                        elif data in ('}', ')', ']'):
                            if not balancing_stack:
                                raise TemplateSyntaxError('unexpected "%s"' %
                                                          data, lineno,
                                                          filename)
                            expected_op = balancing_stack.pop()
                            if expected_op != data:
                                raise TemplateSyntaxError('unexpected "%s", '
                                                          'expected "%s"' %
                                                          (data, expected_op),
                                                          lineno, filename)
                    # yield items
                    if tokens is not None:
                        yield lineno, tokens, data
                    lineno += data.count('\n')

                # fetch new position into new variable so that we can check
                # if there is a internal parsing error which would result
                # in an infinite loop
                pos2 = m.end()

                # handle state changes
                if new_state is not None:
                    # remove the uppermost state
                    if new_state == '#pop':
                        stack.pop()
                    # resolve the new state by group checking
                    elif new_state == '#bygroup':
                        for key, value in m.groupdict().iteritems():
                            if value is not None:
                                stack.append(key)
                                break
                        else:
                            raise RuntimeError('%r wanted to resolve the '
                                               'new state dynamically but'
                                               ' no group matched' %
                                               regex)
                    # direct state name given
                    else:
                        stack.append(new_state)
                    statetokens = self.rules[stack[-1]]
                # we are still at the same position and no stack change.
                # this means a loop without break condition, avoid that and
                # raise error
                elif pos2 == pos:
                    raise RuntimeError('%r yielded empty string without '
                                       'stack change' % regex)
                # publish new function and start again
                pos = pos2
                break
            # if loop terminated without break we havn't found a single match
            # either we are at the end of the file or we have a problem
            else:
                # end of text
                if pos >= source_length:
                    return
                # something went wrong
                raise TemplateSyntaxError('unexpected char %r at %d' %
                                          (source[pos], pos), lineno,
                                          filename)
