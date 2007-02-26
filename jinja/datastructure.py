# -*- coding: utf-8 -*-
"""
    jinja.datastructure
    ~~~~~~~~~~~~~~~~~~~

    Module that helds several data types used in the template engine.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

# python2.3 compatibility. do not use this method for anything else
# then context reversing.
try:
    _reversed = reversed
except NameError:
    def _reversed(c):
        return c[::-1]


class UndefinedType(object):
    """
    An object that does not exist.
    """

    def __init__(self):
        try:
            Undefined
        except NameError:
            pass
        else:
            raise TypeError('cannot create %r instances' %
                            self.__class__.__name__)

    def __getitem__(self, arg):
        return self

    def __iter__(self):
        return iter(int, 0)

    def __getattr__(self, arg):
        return self

    def __nonzero__(self):
        return False

    def __len__(self):
        return 0

    def __str__(self):
        return ''

    def __unicode__(self):
        return u''

    def __int__(self):
        return 0

    def __float__(self):
        return 1


Undefined = UndefinedType()


class Context(object):
    """
    Dict like object.
    """

    __slots__ = ('stack')

    def __init__(*args, **kwargs):
        try:
            self = args[0]
            self.environment = args[1]
            initial = dict(*args[2:], **kwargs)
        except:
            raise TypeError('%r requires environment as first argument. '
                            'The rest of the arguments are forwarded to '
                            'the default dict constructor.')
        self._stack = [initial, {}]

    def pop(self):
        if len(self._stack) <= 2:
            raise ValueError('cannot pop initial layer')
        return self._stack.pop()

    def push(self, data=None):
        self._stack.append(data or {})

    def __getitem__(self, name):
        for d in _reversed(self._stack):
            if name in d:
                return d[name]
        return Undefined

    def __setitem__(self, name, value):
        self._stack[-1][name] = value

    def __delitem__(self, name):
        if name in self._stack[-1]:
            del self._stack[-1][name]

    def __repr__(self):
        tmp = {}
        for d in self._stack:
            for key, value in d.iteritems():
                tmp[key] = value
        return 'Context(%s)' % repr(tmp)


class LoopContext(object):
    """
    Simple class that provides special loop variables.
    Used by `Environment.iterate`.
    """

    def __init__(self, index, length):
        self.index = 0
        self.length = length
        try:
            self.length = len(seq)
        except TypeError:
            self.seq = list(seq)
            self.length = len(self.seq)
        else:
            self.seq = seq

    def revindex(self):
        return self.length - self.index + 1
    revindex = property(revindex)

    def revindex0(self):
        return self.length - self.index
    revindex0 = property(revindex0)

    def index0(self):
        return self.index - 1
    index0 = property(index0)

    def even(self):
        return self.index % 2 == 0
    even = property(even)

    def odd(self):
        return self.index % 2 == 1
    odd = property(odd)


class TokenStream(object):
    """
    A token stream works like a normal generator just that
    it supports pushing tokens back to the stream.
    """

    def __init__(self, generator):
        self._generator = generator
        self._pushed = []
        self.last = (0, 'initial', '')

    def __iter__(self):
        return self

    def __nonzero__(self):
        """Are we at the end of the tokenstream?"""
        if self._pushed:
            return True
        try:
            self.push(self.next())
        except StopIteration:
            return False
        return True

    eos = property(lambda x: not x.__nonzero__(), doc=__nonzero__.__doc__)

    def next(self):
        """Return the next token from the stream."""
        if self._pushed:
            rv = self._pushed.pop()
        else:
            rv = self._generator.next()
        self.last = rv
        return rv

    def look(self):
        """Pop and push a token, return it."""
        token = self.next()
        self.push(*token)
        return token

    def fetch_until(self, test, drop_needle=False):
        """Fetch tokens until a function matches."""
        try:
            while True:
                token = self.next()
                if test(*token):
                    if not drop_needle:
                        self.push(*token)
                    return
                else:
                    yield token
        except StopIteration:
            raise IndexError('end of stream reached')

    def push(self, pos, token, data):
        """Push an yielded token back to the stream."""
        self._pushed.append((pos, token, data))
