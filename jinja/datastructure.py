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
    __slots__ = ()

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


class Deferred(object):
    """
    Object marking an deferred value. Deferred objects are
    objects that are called first access in the context.
    """

    def __init__(self, factory):
        self.factory = factory

    def __call__(self, context, name):
        return self.factory(context, name)


class Context(object):
    """
    Dict like object.
    """

    def __init__(self, _environment_, *args, **kwargs):
        self.environment = _environment_
        self._stack = [self.environment.globals, dict(*args, **kwargs), {}]
        self.globals, _, self.current = self._stack

    def pop(self):
        if len(self._stack) <= 2:
            raise ValueError('cannot pop initial layer')
        rv = self._stack.pop()
        self.current = self._stack[-1]
        return rv

    def push(self, data=None):
        self._stack.append(data or {})
        self.current = self._stack[-1]

    def to_dict(self):
        """
        Convert the context into a dict. This skips the globals.
        """
        result = {}
        for layer in self._stack[1:]:
            for key, value in layer.iteritems():
                result[key] = value
        return result

    def __getitem__(self, name):
        # don't give access to jinja internal variables
        if name.startswith('::'):
            return Undefined
        for d in _reversed(self._stack):
            if name in d:
                rv = d[name]
                if isinstance(rv, Deferred):
                    d[name] = rv = rv(self, name)
                return rv
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

    jinja_allowed_attributes = ['index', 'index0', 'length', 'parent',
                                'even', 'odd']

    def __init__(self, seq, parent, loop_function):
        self.loop_function = loop_function
        self.parent = parent
        self._stack = []
        if seq is not None:
            self.push(seq)

    def push(self, seq):
        self._stack.append({
            'index':            -1,
            'seq':              seq,
            'length':           len(seq)
        })

    def pop(self):
        return self._stack.pop()

    iterated = property(lambda s: s._stack[-1]['index'] > -1)
    index0 = property(lambda s: s._stack[-1]['index'])
    index = property(lambda s: s._stack[-1]['index'] + 1)
    length = property(lambda s: s._stack[-1]['length'])
    even = property(lambda s: s._stack[-1]['index'] % 2 == 0)
    odd = property(lambda s: s._stack[-1]['index'] % 2 == 1)

    def __iter__(self):
        s = self._stack[-1]
        for idx, item in enumerate(s['seq']):
            s['index'] = idx
            yield item

    def __len__(self):
        return self._stack[-1]['length']

    def __call__(self, seq):
        if self.loop_function is not None:
            return self.loop_function(seq)
        return Undefined


class CycleContext(object):
    """
    Helper class used for cycling.
    """

    def __init__(self, seq=None):
        self.lineno = -1
        if seq is not None:
            self.seq = seq
            self.length = len(seq)
            self.cycle = self.cycle_static
        else:
            self.cycle = self.cycle_dynamic

    def cycle_static(self):
        self.lineno = (self.lineno + 1) % self.length
        return self.seq[self.lineno]

    def cycle_dynamic(self, seq):
        self.lineno = (self.lineno + 1) % len(seq)
        return seq[self.lineno]


class TokenStream(object):
    """
    A token stream works like a normal generator just that
    it supports pushing tokens back to the stream.
    """

    def __init__(self, generator):
        self._generator = generator
        self._pushed = []
        self.last = (1, 'initial', '')

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

    def push(self, lineno, token, data):
        """Push an yielded token back to the stream."""
        self._pushed.append((lineno, token, data))
