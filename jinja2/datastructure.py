# -*- coding: utf-8 -*-
"""
    jinja2.datastructure
    ~~~~~~~~~~~~~~~~~~~~

    Module that helds several data types used in the template engine.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from operator import itemgetter
from collections import deque
from jinja2.exceptions import TemplateSyntaxError, TemplateRuntimeError


_missing = object()


class Token(tuple):
    """
    Token class.
    """
    __slots__ = ()
    lineno, type, value = (property(itemgetter(x)) for x in range(3))

    def __new__(cls, lineno, type, value):
        return tuple.__new__(cls, (lineno, intern(str(type)), value))

    def __str__(self):
        from jinja.lexer import keywords, reverse_operators
        if self.type in keywords:
            return self.type
        elif self.type in reverse_operators:
            return reverse_operators[self.type]
        return self.value

    def __repr__(self):
        return 'Token(%r, %r, %r)' % (
            self.lineno,
            self.type,
            self.value
        )


class TokenStreamIterator(object):
    """
    The iterator for tokenstreams.  Iterate over the stream
    until the eof token is reached.
    """

    def __init__(self, stream):
        self._stream = stream

    def __iter__(self):
        return self

    def next(self):
        token = self._stream.current
        if token.type == 'eof':
            self._stream.close()
            raise StopIteration()
        self._stream.next()
        return token


class TokenStream(object):
    """
    A token stream wraps a generator and supports pushing tokens back.
    It also provides some functions to expect tokens and similar stuff.

    Important note: Do never push more than one token back to the
                    stream.  Although the stream object won't stop you
                    from doing so, the behavior is undefined. Multiple
                    pushed tokens are only used internally!
    """

    def __init__(self, generator, filename):
        self._next = generator.next
        self._pushed = deque()
        self.current = Token(1, 'initial', '')
        self.filename = filename
        self.next()

    def __iter__(self):
        return TokenStreamIterator(self)

    def __nonzero__(self):
        """Are we at the end of the tokenstream?"""
        return bool(self._pushed) or self.current.type != 'eof'

    eos = property(lambda x: not x.__nonzero__(), doc=__nonzero__.__doc__)

    def push(self, token):
        """Push a token back to the stream."""
        self._pushed.append(token)

    def look(self):
        """Look at the next token."""
        old_token = self.current
        next = self.next()
        self.push(old_token)
        self.push(next)
        return next

    def skip(self, n):
        """Got n tokens ahead."""
        for x in xrange(n):
            self.next()

    def next(self):
        """Go one token ahead."""
        if self._pushed:
            self.current = self._pushed.popleft()
        elif self.current.type != 'eof':
            try:
                self.current = self._next()
            except StopIteration:
                self.close()

    def close(self):
        """Close the stream."""
        self.current = Token(self.current.lineno, 'eof', '')
        self._next = None

    def expect(self, token_type, token_value=_missing):
        """Expect a given token type and return it"""
        if self.current.type is not token_type:
            raise TemplateSyntaxError("expected token %r, got %r" %
                                      (token_type, self.current.type),
                                      self.current.lineno,
                                      self.filename)
        elif token_value is not _missing and \
             self.current.value != token_value:
            raise TemplateSyntaxError("expected %r, got %r" %
                                      (token_value, self.current.value),
                                      self.current.lineno,
                                      self.filename)
        try:
            return self.current
        finally:
            self.next()
