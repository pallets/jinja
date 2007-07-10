# -*- coding: utf-8 -*-
"""
    jinja.utils
    ~~~~~~~~~~~

    Utility functions.

    **license information**: some of the regular expressions and
    the ``urlize`` function were taken from the django framework.

    :copyright: 2007 by Armin Ronacher, Lawrence Journal-World.
    :license: BSD, see LICENSE for more details.
"""
import re
import sys
import string
from types import MethodType, FunctionType
from compiler.ast import CallFunc, Name, Const
from jinja.nodes import Trans
from jinja.exceptions import SecurityException, TemplateNotFound

# the python2.4 version of deque is missing the remove method
# because a for loop with a lookup for the missing value written
# in python is slower we just use deque if we have python2.5 or higher
try:
    from collections import deque
    deque.remove
except (ImportError, AttributeError):
    class deque(list):
        """
        Minimal subclass of list that provides the deque
        interface used by the native `BaseContext` and the
        `CacheDict`
        """
        def appendleft(self, item):
            list.insert(self, 0, item)
        def popleft(self):
            return list.pop(self, 0)
        def clear(self):
            del self[:]

# support for a working reversed() in 2.3
try:
    reversed = reversed
except NameError:
    def reversed(iterable):
        if hasattr(iterable, '__reversed__'):
            return iterable.__reversed__()
        try:
            return iter(iterable[::-1])
        except TypeError:
            return iter(tuple(iterable)[::-1])

# set support for python 2.3
try:
    set = set
except NameError:
    from sets import Set as set

# sorted support (just a simplified version)
try:
    sorted = sorted
except NameError:
    _cmp = cmp
    def sorted(seq, cmp=None, key=None, reverse=False):
        rv = list(seq)
        if key is not None:
            cmp = lambda a, b: _cmp(key(a), key(b))
        rv.sort(cmp)
        if reverse:
            rv.reverse()
        return rv

# if we have extended debugger support we should really use it
try:
    from jinja._tbtools import *
    has_extended_debugger = True
except ImportError:
    has_extended_debugger = False

# group by support
try:
    from itertools import groupby
except ImportError:
    class groupby(object):

        def __init__(self, iterable, key=lambda x: x):
            self.keyfunc = key
            self.it = iter(iterable)
            self.tgtkey = self.currkey = self.currvalue = xrange(0)

        def __iter__(self):
            return self

        def next(self):
            while self.currkey == self.tgtkey:
                self.currvalue = self.it.next()
                self.currkey = self.keyfunc(self.currvalue)
            self.tgtkey = self.currkey
            return (self.currkey, self._grouper(self.tgtkey))

        def _grouper(self, tgtkey):
            while self.currkey == tgtkey:
                yield self.currvalue
                self.currvalue = self.it.next()
                self.currkey = self.keyfunc(self.currvalue)

#: function types
callable_types = (FunctionType, MethodType)

#: number of maximal range items
MAX_RANGE = 1000000

_word_split_re = re.compile(r'(\s+)')

_punctuation_re = re.compile(
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' %  (
        '|'.join([re.escape(p) for p in ('(', '<', '&lt;')]),
        '|'.join([re.escape(p) for p in ('.', ',', ')', '>', '\n', '&gt;')])
    )
)

_simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')

#: used by from_string as cache
_from_string_env = None


def escape(s, quote=None):
    """
    SGML/XML escape an unicode object.
    """
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if not quote:
        return s
    return s.replace('"', "&quot;")


def urlize(text, trim_url_limit=None, nofollow=False):
    """
    Converts any URLs in text into clickable links. Works on http://,
    https:// and www. links. Links can have trailing punctuation (periods,
    commas, close-parens) and leading punctuation (opening parens) and
    it'll still do the right thing.

    If trim_url_limit is not None, the URLs in link text will be limited
    to trim_url_limit characters.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None \
                         and (x[:limit] + (len(x) >=limit and '...'
                         or '')) or x
    words = _word_split_re.split(text)
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = _punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            if middle.startswith('www.') or (
                '@' not in middle and
                not middle.startswith('http://') and
                len(middle) > 0 and
                middle[0] in string.letters + string.digits and (
                    middle.endswith('.org') or
                    middle.endswith('.net') or
                    middle.endswith('.com')
                )):
                middle = '<a href="http://%s"%s>%s</a>' % (middle,
                    nofollow_attr, trim_url(middle))
            if middle.startswith('http://') or \
               middle.startswith('https://'):
                middle = '<a href="%s"%s>%s</a>' % (middle,
                    nofollow_attr, trim_url(middle))
            if '@' in middle and not middle.startswith('www.') and \
               not ':' in middle and _simple_email_re.match(middle):
                middle = '<a href="mailto:%s">%s</a>' % (middle, middle)
            if lead + middle + trail != word:
                words[i] = lead + middle + trail
    return u''.join(words)


def from_string(source):
    """
    Create a template from the template source.
    """
    global _from_string_env
    if _from_string_env is None:
        from jinja.environment import Environment
        _from_string_env = Environment()
    return _from_string_env.from_string(source)


#: minor speedup
_getattr = getattr

def get_attribute(obj, name):
    """
    Return the attribute from name. Raise either `AttributeError`
    or `SecurityException` if something goes wrong.
    """
    if not isinstance(name, basestring):
        raise AttributeError(name)
    if name[:2] == name[-2:] == '__':
        raise SecurityException('not allowed to access internal attributes')
    if obj.__class__ in callable_types and name.startswith('func_') or \
       name.startswith('im_'):
        raise SecurityException('not allowed to access function attributes')
    r = _getattr(obj, 'jinja_allowed_attributes', None)
    if r is not None and name not in r:
        raise SecurityException('disallowed attribute accessed')
    return _getattr(obj, name)


def safe_range(start, stop=None, step=None):
    """
    "Safe" form of range that does not generate too large lists.
    """
    # this also works with None since None is always smaller than
    # any other value.
    if start > MAX_RANGE:
        start = MAX_RANGE
    if stop > MAX_RANGE:
        stop = MAX_RANGE
    if step is None:
        step = 1
    if stop is None:
        return range(0, start, step)
    return range(start, stop, step)


def generate_lorem_ipsum(n=5, html=True, min=20, max=100):
    """
    Generate some lorem impsum for the template.
    """
    from jinja.constants import LOREM_IPSUM_WORDS
    from random import choice, random, randrange
    words = LOREM_IPSUM_WORDS.split()
    result = []

    for _ in xrange(n):
        next_capitalized = True
        last_comma = last_fullstop = 0
        word = None
        last = None
        p = []

        # each paragraph contains out of 20 to 100 words.
        for idx, _ in enumerate(xrange(randrange(min, max))):
            while True:
                word = choice(words)
                if word != last:
                    last = word
                    break
            if next_capitalized:
                word = word.capitalize()
                next_capitalized = False
            # add commas
            if idx - randrange(3, 8) > last_comma:
                last_comma = idx
                last_fullstop += 2
                word += ','
            # add end of sentences
            if idx - randrange(10, 20) > last_fullstop:
                last_comma = last_fullstop = idx
                word += '.'
                next_capitalized = True
            p.append(word)

        # ensure that the paragraph ends with a dot.
        p = u' '.join(p)
        if p.endswith(','):
            p = p[:-1] + '.'
        elif not p.endswith('.'):
            p += '.'
        result.append(p)

    if not html:
        return u'\n\n'.join(result)
    return u'\n'.join([u'<p>%s</p>' % escape(x) for x in result])


def watch_changes(env, context, iterable, *attributes):
    """
    Wise replacement for ``{% ifchanged %}``.
    """
    # find the attributes to watch
    if attributes:
        tests = []
        tmp = []
        for attribute in attributes:
            if isinstance(attribute, (str, unicode, int, long, bool)):
                tmp.append(attribute)
            else:
                tests.append(tuple(attribute))
        if tmp:
            tests.append(tuple(attribute))
        last = tuple([object() for x in tests])
    # or no attributes if we watch the object itself
    else:
        tests = None
        last = object()

    # iterate trough it and keep check the attributes or values
    for item in iterable:
        if tests is None:
            cur = item
        else:
            cur = tuple([env.get_attributes(item, x) for x in tests])
        if cur != last:
            changed = True
            last = cur
        else:
            changed = False
        yield changed, item
watch_changes.jinja_context_callable = True


def render_included(env, context, template_name):
    """
    Works like djangos {% include %} tag. It doesn't include the
    template but load it independently and renders it to a string.
    """
    #XXX: ignores parent completely!
    tmpl = env.get_template(template_name)
    return tmpl.render(context.to_dict())
render_included.jinja_context_callable = True


# python2.4 and lower has a bug regarding joining of broken generators.
# because of the runtime debugging system we have to keep track of the
# number of frames to skip. that's what RUNTIME_EXCEPTION_OFFSET is for.
try:
    _test_singleton = object()
    def _test_gen_bug():
        raise TypeError(_test_singleton)
        yield None
    ''.join(_test_gen_bug())
except TypeError, e:
    if e.args and e.args[0] is _test_singleton:
        capture_generator = u''.join
        RUNTIME_EXCEPTION_OFFSET = 1
    else:
        capture_generator = lambda gen: u''.join(tuple(gen))
        RUNTIME_EXCEPTION_OFFSET = 2
del _test_singleton, _test_gen_bug


def buffereater(f):
    """
    Used by the python translator to capture output of substreams.
    (macros, filter sections etc)
    """
    return lambda *a, **kw: capture_generator(f(*a, **kw))


def empty_block(context):
    """
    An empty callable that just returns an empty decorator.
    Used to represent empty blocks.
    """
    if 0: yield None


def collect_translations(ast):
    """
    Collect all translatable strings for the given ast. The
    return value is a list of tuples in the form ``(lineno, singular,
    plural)``. If a translation doesn't require a plural form the
    third item is `None`.
    """
    todo = [ast]
    result = []
    while todo:
        node = todo.pop()
        if node.__class__ is Trans:
            result.append((node.lineno, node.singular, node.plural))
        elif node.__class__ is CallFunc and \
             node.node.__class__ is Name and \
             node.node.name == '_':
            if len(node.args) == 1 and node.args[0].__class__ is Const:
                result.append((node.lineno, node.args[0].value, None))
        todo.extend(node.getChildNodes())
    result.sort(lambda a, b: cmp(a[0], b[0]))
    return result


class DebugHelper(object):
    """
    Debugging Helper. Available in the template as "debug".
    """
    jinja_context_callable = True
    jinja_allowed_attributes = ['filters']

    def __init__(self):
        raise TypeError('cannot create %r instances' %
                        self.__class__.__name__)

    def __call__(self, env, context):
        """Print a nice representation of the context."""
        from pprint import pformat
        return pformat(context.to_dict())

    def filters(self, env, context, builtins=True):
        """List the filters."""
        from inspect import getdoc
        strip = set()
        if not builtins:
            from jinja.defaults import DEFAULT_FILTERS
            strip = set(DEFAULT_FILTERS.values())
        filters = env.filters.items()
        filters.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        result = []
        for name, f in filters:
            if f in strip:
                continue
            doc = '\n'.join(['    ' + x for x in (getdoc(f) or '').splitlines()])
            result.append('`%s`\n\n%s' % (name, doc))
        return '\n\n'.join(result)
    filters.jinja_context_callable = True

    def tests(self, env, context, builtins=True):
        """List the tests."""
        from inspect import getdoc
        strip = set()
        if not builtins:
            from jinja.defaults import DEFAULT_TESTS
            strip = set(DEFAULT_TESTS.values())
        tests = env.tests.items()
        tests.sort(lambda a, b: cmp(a[0].lower(), b[0].lower()))
        result = []
        for name, f in tests:
            if f in strip:
                continue
            doc = '\n'.join(['    ' + x for x in (getdoc(f) or '').splitlines()])
            result.append('`%s`\n\n%s' % (name, doc))
        return '\n\n'.join(result)
    tests.jinja_context_callable = True

    def __str__(self):
        print 'use debug() for debugging the context'


#: the singleton instance of `DebugHelper`
debug_helper = object.__new__(DebugHelper)


class CacheDict(object):
    """
    A dict like object that stores a limited number of items and forgets
    about the least recently used items::

        >>> cache = CacheDict(3)
        >>> cache['A'] = 0
        >>> cache['B'] = 1
        >>> cache['C'] = 2
        >>> len(cache)
        3

    If we now access 'A' again it has a higher priority than B::

        >>> cache['A']
        0

    If we add a new item 'D' now 'B' will disappear::

        >>> cache['D'] = 3
        >>> len(cache)
        3
        >>> 'B' in cache
        False

    If you iterate over the object the most recently used item will be
    yielded First::

        >>> for item in cache:
        ...     print item
        D
        A
        C

    If you want to iterate the other way round use ``reverse(cache)``.

    Implementation note: This is not a nice way to solve that problem but
    for smaller capacities it's faster than a linked list.
    Perfect for template environments where you don't expect too many
    different keys.
    """

    def __init__(self, capacity):
        self.capacity = capacity
        self._mapping = {}
        self._queue = deque()

        # alias all queue methods for faster lookup
        self._popleft = self._queue.popleft
        self._pop = self._queue.pop
        self._remove = self._queue.remove
        self._append = self._queue.append

    def copy(self):
        """
        Return an shallow copy of the instance.
        """
        rv = CacheDict(self.capacity)
        rv._mapping.update(self._mapping)
        rv._queue = self._queue[:]
        return rv

    def get(self, key, default=None):
        """
        Return an item from the cache dict or `default`
        """
        if key in self:
            return self[key]
        return default

    def setdefault(self, key, default=None):
        """
        Set `default` if the key is not in the cache otherwise
        leave unchanged. Return the value of this key.
        """
        if key in self:
            return self[key]
        self[key] = default
        return default

    def clear(self):
        """
        Clear the cache dict.
        """
        self._mapping.clear()
        self._queue.clear()

    def __contains__(self, key):
        """
        Check if a key exists in this cache dict.
        """
        return key in self._mapping

    def __len__(self):
        """
        Return the current size of the cache dict.
        """
        return len(self._mapping)

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._mapping
        )

    def __getitem__(self, key):
        """
        Get an item from the cache dict. Moves the item up so that
        it has the highest priority then.

        Raise an `KeyError` if it does not exist.
        """
        rv = self._mapping[key]
        if self._queue[-1] != key:
            self._remove(key)
            self._append(key)
        return rv

    def __setitem__(self, key, value):
        """
        Sets the value for an item. Moves the item up so that it
        has the highest priority then.
        """
        if key in self._mapping:
            self._remove(key)
        elif len(self._mapping) == self.capacity:
            del self._mapping[self._popleft()]
        self._append(key)
        self._mapping[key] = value

    def __delitem__(self, key):
        """
        Remove an item from the cache dict.
        Raise an `KeyError` if it does not exist.
        """
        del self._mapping[key]
        self._remove(key)

    def __iter__(self):
        """
        Iterate over all values in the cache dict, ordered by
        the most recent usage.
        """
        return reversed(self._queue)

    def __reversed__(self):
        """
        Iterate over the values in the cache dict, oldest items
        coming first.
        """
        return iter(self._queue)

    __copy__ = copy

    def __deepcopy__(self):
        """
        Return a deep copy of the cache dict.
        """
        from copy import deepcopy
        rv = CacheDict(self.capacity)
        rv._mapping = deepcopy(self._mapping)
        rv._queue = deepcopy(self._queue)
        return rv
