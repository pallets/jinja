# -*- coding: utf-8 -*-
"""
    jinja.lexer
    ~~~~~~~~~~~
"""
import re
from jinja.datastructure import TokenStream
from jinja.exceptions import TemplateSyntaxError


# static regular expressions
whitespace_re = re.compile(r'\s+(?m)')
name_re = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*[!?]?')
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")(?ms)')
number_re = re.compile(r'\d+(\.\d+)*')

operator_re = re.compile('(%s)' % '|'.join(
    isinstance(x, unicode) and str(x) or re.escape(x) for x in [
    # math operators
    '+', '-', '*', '/', '%',
    # braces and parenthesis
    '[', ']', '(', ')', '{', '}',
    # attribute access and comparison / logical operators
    '.', ',', '|', '==', '<', '>', '<=', '>=', '!=',
    ur'or\b', ur'and\b', ur'not\b'
]))


class Failure(object):
    """
    Class that raises a `TemplateSyntaxError` if called.
    Used by the `Lexer` to specify known errors.
    """

    def __init__(self, message, cls=TemplateSyntaxError):
        self.message = message
        self.error_class = cls

    def __call__(self, position):
        raise self.error_class(self.message, position)


class Lexer(object):
    """
    Class that implements a lexer for a given environment. Automatically
    created by the environment class, usually you don't have to do that.
    """

    def __init__(self, environment):
        # shortcuts
        c = lambda x: re.compile(x, re.M | re.S)
        e = re.escape

        # parsing rules for tags
        tag_rules = [
            (whitespace_re, None, None),
            (number_re, 'number', None),
            (operator_re, 'operator', None),
            (name_re, 'name', None),
            (string_re, 'string', None)
        ]

        # global parsing rules
        self.rules = {
            'root': [
                (c('(.*?)(?:(?P<comment_begin>' +
                    e(environment.comment_start_string) +
                    ')|(?P<block_begin>' +
                    e(environment.block_start_string) +
                    ')|(?P<variable_begin>' +
                    e(environment.variable_start_string) +
                   '))'), ('data', '#bygroup'), '#bygroup'),
                (c('.+'), 'data', None)
            ],
            'comment_begin': [
                (c(r'(.*?)(%s)' % e(environment.comment_end_string)),
                 ('comment', 'comment_end'), '#pop'),
                (c('(.)'), (Failure('Missing end of comment tag'),), None)
            ],
            'block_begin': [
                (c(e(environment.block_end_string)), 'block_end', '#pop')
            ] + tag_rules,
            'variable_begin': [
                (c(e(environment.variable_end_string)), 'variable_end',
                 '#pop')
            ] + tag_rules
        }

    def tokenize(self, source):
        """
        Simple tokenize function that yields ``(position, type, contents)``
        tuples. Wrap the generator returned by this function in a
        `TokenStream` to get real token instances and be able to push tokens
        back to the stream. That's for example done by the parser.
        """
        return TokenStream(self.tokeniter(source))

    def tokeniter(self, source):
        """
        This method tokenizes the text and returns the tokens in a generator.
        Normally it's a better idea to use the `tokenize` function which
        returns a `TokenStream` but in some situations it can be useful
        to use this function since it can be marginally faster.
        """
        pos = 0
        stack = ['root']
        statetokens = self.rules['root']
        source_length = len(source)

        while True:
            # tokenizer loop
            for regex, tokens, new_state in statetokens:
                m = regex.match(source, pos)
                if m:
                    # tuples support more options
                    if isinstance(tokens, tuple):
                        for idx, token in enumerate(tokens):
                            # hidden group
                            if token is None:
                                continue
                            # failure group
                            elif isinstance(token, Failure):
                                raise token(m.start(idx + 1))
                            # bygroup is a bit more complex, in that case we
                            # yield for the current token the first named
                            # group that matched
                            elif token == '#bygroup':
                                for key, value in m.groupdict().iteritems():
                                    if value is not None:
                                        yield m.start(key), key, value
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
                                    yield m.start(idx + 1), token, data
                    # strings as token just are yielded as it, but just
                    # if the data is not empty
                    else:
                        data = m.group()
                        if tokens is not None:
                            if data:
                                yield pos, tokens, data
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
                                          (source[pos], pos), pos)
