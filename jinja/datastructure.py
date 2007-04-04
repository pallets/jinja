# -*- coding: utf-8 -*-
"""
    jinja.datastructure
    ~~~~~~~~~~~~~~~~~~~

    Module that helds several data types used in the template engine.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

# sets
try:
    set
except NameError:
    from sets import Set as set

from jinja.exceptions import TemplateSyntaxError, TemplateRuntimeError
from cgi import escape

_known_safe_types = set([int, long, float])


def contextcallable(f):
    """
    Mark a function context callable.
    """
    f.jinja_context_callable = True
    return f


def unsafe(f):
    """
    Mark function as unsafe.
    """
    f.jinja_unsafe_call = True
    return f


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

    __sub__ = __mul__ = __div__ = __rsub__ = __rmul__ = __div__ = __radd__ = \
    __add__ = lambda self, other: other

    def __getitem__(self, arg):
        return self

    def __iter__(self):
        if False:
            yield None

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
        return 0.0

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    def __call__(self, *args, **kwargs):
        return self


Undefined = UndefinedType()


class FakeTranslator(object):
    """
    Default null translator.
    """

    def gettext(self, s):
        return s

    def ngettext(self, s, p, n):
        if n == 1:
            return s
        return p


class Deferred(object):
    """
    Object marking an deferred value. Deferred objects are
    objects that are called first access in the context.
    """

    def __init__(self, factory):
        self.factory = factory

    def __call__(self, context, name):
        return self.factory(context.environment, context, name)


class Markup(unicode):
    """
    Compatibility for Pylons and probably some other frameworks.
    """

    def __html__(self):
        return unicode(self)


class TemplateData(Markup):
    """
    Subclass of unicode to mark objects that are coming from the
    template. The autoescape filter can use that.
    """


class Context(object):
    """
    Dict like object.
    """

    def __init__(self, _environment_, *args, **kwargs):
        self.environment = _environment_
        self._stack = [_environment_.globals, dict(*args, **kwargs), {}]
        self.globals, self.initial, self.current = self._stack

        # cache object used for filters and tests
        self.cache = {}

    def pop(self):
        """Pop the last layer from the stack and return it."""
        rv = self._stack.pop()
        self.current = self._stack[-1]
        return rv

    def push(self, data=None):
        """Push a new dict or empty layer to the stack and return that layer"""
        data = data or {}
        self._stack.append(data)
        self.current = self._stack[-1]
        return data

    def to_dict(self):
        """Convert the context into a dict. This skips the globals."""
        result = {}
        for layer in self._stack[1:]:
            for key, value in layer.iteritems():
                if key.startswith('::'):
                    continue
                result[key] = value
        return result

    def __getitem__(self, name):
        if not name.startswith('::'):
            # because the stack is usually quite small we better use [::-1]
            # which is faster than reversed() somehow.
            for d in self._stack[::-1]:
                if name in d:
                    rv = d[name]
                    if rv.__class__ is Deferred:
                        rv = rv(self, name)
                        # never touch the globals!
                        if d is self.globals:
                            self.initial[name] = rv
                        else:
                            d[name] = rv
                    return rv
        if self.environment.silent:
            return Undefined
        raise TemplateRuntimeError('%r is not defined' % name)

    def __setitem__(self, name, value):
        self.current[name] = value

    def __delitem__(self, name):
        if name in self.current:
            del self.current[name]

    def __contains__(self, name):
        for layer in self._stack:
            if name in layer:
                return True
        return False

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
                                'even', 'odd', 'revindex0', 'revindex',
                                'first', 'last']

    def __init__(self, seq, parent, loop_function):
        self.loop_function = loop_function
        self.parent = parent
        self._stack = []
        if seq is not None:
            self.push(seq)

    def push(self, seq):
        """
        Push a sequence to the loop stack. This is used by the
        recursive for loop.
        """
        if seq in (Undefined, None):
            seq = ()
        self._stack.append({
            'index':            -1,
            'seq':              seq,
            'length':           len(seq)
        })
        return self

    def pop(self):
        """Remove the last layer from the loop stack."""
        return self._stack.pop()

    iterated = property(lambda s: s._stack[-1]['index'] > -1)
    index0 = property(lambda s: s._stack[-1]['index'])
    index = property(lambda s: s._stack[-1]['index'] + 1)
    revindex0 = property(lambda s: s._stack[-1]['length'] -
                                   s._stack[-1]['index'] - 1)
    revindex = property(lambda s: s._stack[-1]['length'] -
                                  s._stack[-1]['index'])
    length = property(lambda s: s._stack[-1]['length'])
    even = property(lambda s: s._stack[-1]['index'] % 2 == 1)
    odd = property(lambda s: s._stack[-1]['index'] % 2 == 0)
    first = property(lambda s: s._stack[-1]['index'] == 0)
    last = property(lambda s: s._stack[-1]['index'] ==
                              s._stack[-1]['length'] - 1)

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
        raise TemplateRuntimeError('In order to make loops callable you have '
                                   'to define them with the "recursive" '
                                   'modifier.')

    def __repr__(self):
        if self._stack:
            return '<LoopContext %d/%d%s>' % (
                self.index,
                self.length,
                self.loop_function is not None and ' recursive' or ''
            )
        return '<LoopContext (empty)>'


class CycleContext(object):
    """
    Helper class used for cycling.
    """

    def __init__(self, seq=None):
        self.pos = -1
        # bind the correct helper function based on the constructor signature
        if seq is not None:
            self.seq = seq
            self.length = len(seq)
            self.cycle = self.cycle_static
        else:
            self.cycle = self.cycle_dynamic

    def cycle_static(self):
        """Helper function for static cycling."""
        self.pos = (self.pos + 1) % self.length
        return self.seq[self.pos]

    def cycle_dynamic(self, seq):
        """Helper function for dynamic cycling."""
        self.pos = pos = (self.pos + 1) % len(seq)
        return seq[pos]


class SuperBlock(object):
    """
    Helper class for ``{{ super() }}``.
    """
    jinja_allowed_attributes = ['name']

    def __init__(self, name, blocks, level, context):
        self.name = name
        self.context = context
        if name in blocks:
            self.stack = blocks[name]
            self.level = level
        else:
            self.stack = None

    def __call__(self, offset=1):
        if self.stack is not None:
            level = self.level + (offset - 1)
            if level < len(self.stack):
                return self.stack[level](self.context)
        raise TemplateRuntimeError('no super block for %r' % self.name)

    def __repr__(self):
        return '<SuperBlock %r>' % self.name


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
            raise TemplateSyntaxError('end of stream reached')

    def drop_until(self, test, drop_needle=False):
        """Fetch tokens until a function matches and drop all
        tokens."""
        for token in self.fetch_until(test, drop_needle):
            pass

    def push(self, lineno, token, data):
        """Push an yielded token back to the stream."""
        self._pushed.append((lineno, token, data))
