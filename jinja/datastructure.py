# -*- coding: utf-8 -*-
"""
    jinja.datastructure
    ~~~~~~~~~~~~~~~~~~~

    Module that helds several data types used in the template engine.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from jinja.exceptions import TemplateSyntaxError, TemplateRuntimeError


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


def make_undefined(implementation):
    """
    Creates an undefined singleton based on a given implementation.
    It performs some tests that make sure the undefined type implements
    everything it should.
    """
    self = object.__new__(implementation)
    self.__reduce__()
    return self


class AbstractUndefinedType(object):
    """
    Base class for any undefined type.
    """
    __slots__ = ()

    def __init__(self):
        raise TypeError('cannot create %r instances' %
                        self.__class__.__name__)

    def __setattr__(self, name, value):
        raise AttributeError('%r object has no attribute %r' % (
            self.__class__.__name__,
            name
        ))

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __copy__(self):
        return self
    __deepcopy__ = __copy__

    def __repr__(self):
        return 'Undefined'

    def __reduce__(self):
        raise TypeError('undefined objects have to provide a __reduce__')


class SilentUndefinedType(AbstractUndefinedType):
    """
    An object that does not exist.
    """
    __slots__ = ()

    def __add__(self, other):
        """Any operator returns the operand."""
        return other
    __sub__ = __mul__ = __div__ = __rsub__ = __rmul__ = __div__ = __mod__ =\
    __radd__ = __rmod__ = __add__

    def __getitem__(self, arg):
        """Getting any item returns `Undefined`"""
        return self

    def __iter__(self):
        """Iterating over `Undefined` returns an empty iterator."""
        if False:
            yield None

    def __getattr__(self, arg):
        """Getting any attribute returns `Undefined`"""
        return self

    def __nonzero__(self):
        """`Undefined` is considered boolean `False`"""
        return False

    def __len__(self):
        """`Undefined` is an empty sequence"""
        return 0

    def __str__(self):
        """The string representation is empty."""
        return ''

    def __unicode__(self):
        """The unicode representation is empty."""
        return u''

    def __int__(self):
        """Converting `Undefined` to an integer ends up in ``0``"""
        return 0

    def __float__(self):
        """Converting `Undefined` to an float ends up in ``0.0``"""
        return 0.0

    def __call__(self, *args, **kwargs):
        """Calling `Undefined` returns `Undefined`"""
        return self

    def __reduce__(self):
        """Helper for pickle."""
        return 'SilentUndefined'


class ComplainingUndefinedType(AbstractUndefinedType):
    """
    An object that does not exist.
    """
    __slots__ = ()

    def __len__(self):
        """Getting the length raises error."""
        raise TemplateRuntimeError('Operated on undefined object')

    def __iter__(self):
        """Iterating over `Undefined` raises an error."""
        raise TemplateRuntimeError('Iterated over undefined object')

    def __nonzero__(self):
        """`Undefined` is considered boolean `False`"""
        return False

    def __str__(self):
        """The string representation raises an error."""
        raise TemplateRuntimeError('Undefined object rendered')

    def __unicode__(self):
        """The unicode representation raises an error."""
        self.__str__()

    def __call__(self, *args, **kwargs):
        """Calling `Undefined` returns `Undefined`"""
        raise TemplateRuntimeError('Undefined object called')

    def __reduce__(self):
        """Helper for pickle."""
        return 'ComplainingUndefined'


#: the singleton instances for the undefined objects
SilentUndefined = make_undefined(SilentUndefinedType)
ComplainingUndefined = make_undefined(ComplainingUndefinedType)

#: jinja 1.0 compatibility
Undefined = SilentUndefined
UndefinedType = SilentUndefinedType


class FakeTranslator(object):
    """
    Default null translator.
    """

    def gettext(self, s):
        """
        Translate a singular string.
        """
        return s

    def ngettext(self, s, p, n):
        """
        Translate a plural string.
        """
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

    It's only used in Jinja environments with `auto_escape` set
    to true.
    """

    def __html__(self):
        return unicode(self)


class TemplateData(Markup):
    """
    Subclass of unicode to mark objects that are coming from the
    template. The autoescape filter can use that.
    """


# import these here because those modules import Deferred and Undefined
# from this module.
try:
    # try to use the c implementation of the base context if available
    from jinja._speedups import BaseContext
except ImportError:
    # if there is no c implementation we go with a native python one
    from jinja._native import BaseContext


class Context(BaseContext):
    """
    Dict like object containing the variables for the template.
    """

    def __init__(self, *args, **kwargs):
        environment = args[0]
        super(Context, self).__init__(environment.undefined_singleton,
                                      environment.globals,
                                      dict(*args[1:], **kwargs))
        self._translate_func = None
        self.cache = {}
        self.environment = environment

    def to_dict(self):
        """
        Convert the context into a dict. This skips the globals.
        """
        result = {}
        for layer in self.stack[1:]:
            for key, value in layer.iteritems():
                if key.startswith('::'):
                    continue
                result[key] = value
        return result

    def translate_func(self):
        """
        The translation function for this context. It takes
        4 parameters. The singular string, the optional plural one,
        The name of the variable in the replacements dict and the
        replacements dict. This is only used by the i18n system
        internally the simplified version (just one argument) is
        available in the template for the user too.
        """
        if self._translate_func is not None:
            return self._translate_func
        translator = self.environment.get_translator(self)
        gettext = translator.gettext
        ngettext = translator.ngettext
        def translate(s, p=None, n=None, r=None):
            if p is None:
                s = gettext(s)
            else:
                s = ngettext(s, p, r[n])
            # apply replacement substitution only if replacements
            # are given. This is the case for {% trans %}...{% endtrans %}
            # but for the "_()" syntax and a trans tag without a body.
            if r is not None:
                return s % r
            return s
        translate.__doc__ = Context.translate_func.__doc__
        self._translate_func = translate
        return translate
    translate_func = property(translate_func, doc=translate_func.__doc__)

    def __repr__(self):
        """
        String representation of the context.
        """
        return 'Context(%r)' % self.to_dict()


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
        if loop_function is None:
            self.push(seq)

    def push(self, seq):
        """
        Push a sequence to the loop stack. This is used by the
        recursive for loop.
        """
        # iteration over None is catched, but we don't catch iteration
        # over undefined because that behavior is handled in the
        # undefined singleton
        if seq is None:
            seq = ()
            length = 0
        else:
            try:
                length = len(seq)
            except TypeError:
                seq = list(seq)
                length = len(seq)
        self._stack.append({
            'index':            -1,
            'seq':              seq,
            'length':           length
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


class StateTest(object):
    """
    Wrapper class for basic lambdas in order to simplify
    debugging in the parser. It also provides static helper
    functions that replace some lambda expressions
    """

    def __init__(self, func, error_message):
        self.func = func
        self.error_message = error_message

    def __call__(self, p, t, d):
        return self.func(p, t, d)

    def expect_token(token_name, error_message=None):
        """Scans until a token types is found."""
        return StateTest(lambda p, t, d: t == token_name, 'expected ' +
                         (error_message or token_name))
    expect_token = staticmethod(expect_token)

    def expect_name(*names):
        """Scans until one of the given names is found."""
        if len(names) == 1:
            name = names[0]
            return StateTest(lambda p, t, d: t == 'name' and d == name,
                             "expected '%s'" % name)
        else:
            return StateTest(lambda p, t, d: t == 'name' and d in names,
                             'expected one of %s' % ','.join(["'%s'" % name
                             for name in names]))
    expect_name = staticmethod(expect_name)


class TokenStream(object):
    """
    A token stream works like a normal generator just that
    it supports pushing tokens back to the stream.
    """

    def __init__(self, generator, filename):
        self._next = generator.next
        self._pushed = []
        self.last = (1, 'initial', '')
        self.filename = filename

    def bound(self):
        """Return True if the token stream is bound to a parser."""
        return self.parser is not None
    bound = property(bound, doc=bound.__doc__)

    def __iter__(self):
        """Return self in order to mark this is iterator."""
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
            rv = self._next()
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
            if isinstance(test, StateTest):
                msg = ': ' + test.error_message
            else:
                msg = ''
            raise TemplateSyntaxError('end of stream' + msg,
                                      self.last[0], self.filename)

    def drop_until(self, test, drop_needle=False):
        """Fetch tokens until a function matches and drop all
        tokens."""
        for token in self.fetch_until(test, drop_needle):
            pass

    def push(self, lineno, token, data):
        """Push an yielded token back to the stream."""
        self._pushed.append((lineno, token, data))


class TemplateStream(object):
    """
    Wraps a genererator for outputing template streams.
    """

    def __init__(self, gen):
        self._gen = gen
        self._next = gen.next
        self.buffered = False

    def disable_buffering(self):
        """
        Disable the output buffering.
        """
        self._next = self._gen.next
        self.buffered = False

    def enable_buffering(self, size=5):
        """
        Enable buffering. Buffer `size` items before
        yielding them.
        """
        if size <= 1:
            raise ValueError('buffer size too small')
        self.buffered = True

        def buffering_next():
            buf = []
            c_size = 0
            push = buf.append
            next = self._gen.next

            try:
                while True:
                    item = next()
                    if item:
                        push(item)
                        c_size += 1
                    if c_size >= size:
                        raise StopIteration()
            except StopIteration:
                if not c_size:
                    raise
            return u''.join(buf)

        self._next = buffering_next

    def __iter__(self):
        return self

    def next(self):
        return self._next()
