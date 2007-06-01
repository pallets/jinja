# -*- coding: utf-8 -*-
"""
    jinja.lexer
    ~~~~~~~~~~~

    This module implements a Jinja / Python combination lexer. The
    `Lexer` class provided by this module is used to do some preprocessing
    for Jinja.

    On the one hand it filters out invalid operators like the bitshift
    operators we don't allow in templates. On the other hand it separates
    template code and python code in expressions.

    Because of some limitations in the compiler package which are just
    natural but annoying for Jinja, the lexer also "escapes" non names that
    are not keywords. The Jinja parser then removes those escaping marks
    again.

    This is required in order to make "class" and some other python keywords
    we don't use valid identifiers.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja.datastructure import TokenStream
from jinja.exceptions import TemplateSyntaxError
from jinja.utils import set
from weakref import WeakValueDictionary


__all__ = ['Lexer', 'Failure', 'keywords']


# cache for the lexers. Exists in order to be able to have multiple
# environments with the same lexer
_lexer_cache = WeakValueDictionary()


# static regular expressions
whitespace_re = re.compile(r'\s+(?m)')
name_re = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")(?ms)')
number_re = re.compile(r'\d+(\.\d+)*')

operator_re = re.compile('(%s)' % '|'.join([
    isinstance(x, unicode) and str(x) or re.escape(x) for x in [
    # math operators
    '+', '-', '**', '*', '//', '/', '%',
    # braces and parenthesis
    '[', ']', '(', ')', '{', '}',
    # attribute access and comparison / logical operators
    '.', ':', ',', '|', '==', '<=', '>=', '<', '>', '!=', '=',
    ur'or\b', ur'and\b', ur'not\b', ur'in\b', ur'is\b'
]]))

# set of used keywords
keywords = set(['and', 'block', 'cycle', 'elif', 'else', 'endblock',
                'endfilter', 'endfor', 'endif', 'endmacro', 'endraw',
                'endtrans', 'extends', 'filter', 'for', 'if', 'in',
                'include', 'is', 'macro', 'not', 'or', 'pluralize', 'raw',
                'recursive', 'set', 'trans', 'print'])


class Failure(object):
    """
    Class that raises a `TemplateSyntaxError` if called.
    Used by the `Lexer` to specify known errors.
    """

    def __init__(self, message, cls=TemplateSyntaxError):
        self.message = message
        self.error_class = cls

    def __call__(self, lineno, filename):
        raise self.error_class(self.message, lineno, filename)


class LexerMeta(type):
    """
    Metaclass for the lexer that caches instances for
    the same configuration in a weak value dictionary.
    """

    def __call__(cls, environment):
        key = hash((environment.block_start_string,
                    environment.block_end_string,
                    environment.variable_start_string,
                    environment.variable_end_string,
                    environment.comment_start_string,
                    environment.comment_end_string,
                    environment.trim_blocks))

        # use the cached lexer if possible
        if key in _lexer_cache:
            return _lexer_cache[key]

        # create a new lexer and cache it
        lexer = type.__call__(cls, environment)
        _lexer_cache[key] = lexer
        return lexer


class Lexer(object):
    """
    Class that implements a lexer for a given environment. Automatically
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
            (number_re, 'number', None),
            (name_re, 'name', None),
            (operator_re, 'operator', None),
            (string_re, 'string', None)
        ]

        #: if variables and blocks have the same delimiters we won't
        #: receive any variable blocks in the parser. This variable is `True`
        #: if we need that.
        self.no_variable_block = (
            (environment.variable_start_string is
             environment.variable_end_string is None) or
            (environment.variable_start_string ==
             environment.block_start_string and
             environment.variable_end_string ==
             environment.block_end_string)
        )

        # assamble the root lexing rule. because "|" is ungreedy
        # we have to sort by length so that the lexer continues working
        # as expected when we have parsing rules like <% for block and
        # <%= for variables. (if someone wants asp like syntax)
        # variables are just part of the rules if variable processing
        # is required.
        root_tag_rules = [
            ('comment',     environment.comment_start_string),
            ('block',       environment.block_start_string)
        ]
        if not self.no_variable_block:
            root_tag_rules.append(('variable',
                                   environment.variable_start_string))
        root_tag_rules.sort(lambda a, b: cmp(len(b[1]), len(a[1])))

        # block suffix if trimming is enabled
        block_suffix_re = environment.trim_blocks and '\\n?' or ''

        # global lexing rules
        self.rules = {
            'root': [
                # raw directive
                (c('((?:\s*%s\-|%s)\s*raw\s*(?:\-%s\s*|%s%s))' % (
                    e(environment.block_start_string),
                    e(environment.block_start_string),
                    e(environment.block_end_string),
                    e(environment.block_end_string),
                    block_suffix_re
                )), (None,), 'raw'),
                # normal directives
                (c('(.*?)(?:%s)' % '|'.join([
                    '(?P<%s_begin>\s*%s\-|%s)' % (n, e(r), e(r))
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
            # raw block
            'raw': [
                (c('(.*?)((?:\s*%s\-|%s)\s*endraw\s*(?:\-%s\s*|%s%s))' % (
                    e(environment.block_start_string),
                    e(environment.block_start_string),
                    e(environment.block_end_string),
                    e(environment.block_end_string),
                    block_suffix_re
                )), ('data', None), '#pop'),
                (c('(.)'), (Failure('Missing end of raw directive'),), None)
            ]
        }

        # only add the variable rules to the list if we process variables
        # the variable_end_string variable could be None and break things.
        if not self.no_variable_block:
            self.rules['variable_begin'] = [
                (c('\-%s\s*|%s' % (
                    e(environment.variable_end_string),
                    e(environment.variable_end_string)
                )), 'variable_end', '#pop')
            ] + tag_rules

    def tokenize(self, source, filename=None):
        """
        Simple tokenize function that yields ``(position, type, contents)``
        tuples. Wrap the generator returned by this function in a
        `TokenStream` to get real token instances and be able to push tokens
        back to the stream. That's for example done by the parser.

        Additionally non keywords are escaped.
        """
        def generate():
            for lineno, token, value in self.tokeniter(source, filename):
                if token == 'name' and value not in keywords:
                    value += '_'
                yield lineno, token, value
        return TokenStream(generate(), filename)

    def tokeniter(self, source, filename=None):
        """
        This method tokenizes the text and returns the tokens in a generator.
        Use this method if you just want to tokenize a template. The output
        you get is not compatible with the input the jinja parser wants. The
        parser uses the `tokenize` function with returns a `TokenStream` with
        some escaped tokens.
        """
        source = '\n'.join(source.splitlines())
        pos = 0
        lineno = 1
        stack = ['root']
        statetokens = self.rules['root']
        source_length = len(source)

        balancing_stack = []

        while True:
            # tokenizer loop
            for regex, tokens, new_state in statetokens:
                m = regex.match(source, pos)
                # if no match we try again with the next rule
                if not m:
                    continue

                # we only match blocks and variables if brances / parentheses
                # are balanced. continue parsing with the lower rule which
                # is the operator rule. do this only if the end tags look
                # like operators
                if balancing_stack and \
                   tokens in ('variable_end', 'block_end'):
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

                # strings as token just are yielded as it, but just
                # if the data is not empty
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
                        if data:
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
