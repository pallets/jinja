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
import cgi
from types import MethodType, FunctionType
from compiler.ast import CallFunc, Name, Const
from jinja.nodes import Trans
from jinja.datastructure import Context, TemplateData
from jinja.exceptions import SecurityException, TemplateNotFound

#: the python2.4 version of deque is missing the remove method
#: because a for loop with a lookup for the missing value written
#: in python is slower we just use deque if we have python2.5 or higher
if sys.version_info >= (2, 5):
    from collections import deque
else:
    deque = None

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

escape = cgi.escape


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


def get_attribute(obj, name):
    """
    Return the attribute from name. Raise either `AttributeError`
    or `SecurityException` if something goes wrong.
    """
    if not isinstance(name, basestring):
        raise AttributeError(name)
    if name[:2] == name[-2:] == '__' or name[:2] == '::':
        raise SecurityException('not allowed to access internal attributes')
    if (obj.__class__ is FunctionType and name.startswith('func_') or
        obj.__class__ is MethodType and name.startswith('im_')):
        raise SecurityException('not allowed to access function attributes')
    r = getattr(obj, 'jinja_allowed_attributes', None)
    if r is not None and name not in r:
        raise SecurityException('not allowed attribute accessed')
    return getattr(obj, name)


def debug_context(env, context):
    """
    Use this function in templates to get a printed context.
    """
    from pprint import pformat
    return pformat(context.to_dict())
debug_context.jinja_context_callable = True


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


# python2.4 and lower has a bug regarding joining of broken generators.
# because of the runtime debugging system we have to keep track of the
# number of frames to skip. that's what RUNTIME_EXCEPTION_OFFSET is for.
if sys.version_info < (2, 5):
    capture_generator = lambda gen: u''.join(tuple(gen))
    RUNTIME_EXCEPTION_OFFSET = 2

# this should be faster and used in python2.5 and higher
else:
    capture_generator = u''.join
    RUNTIME_EXCEPTION_OFFSET = 1


def buffereater(f):
    """
    Used by the python translator to capture output of substreams.
    (macros, filter sections etc)
    """
    def wrapped(*args, **kwargs):
        return TemplateData(capture_generator(f(*args, **kwargs)))
    return wrapped


def fake_template_exception(exception, filename, lineno, source,
                            context_or_env):
    """
    Raise an exception "in a template". Return a traceback
    object. This is used for runtime debugging, not compile time.
    """
    # some traceback systems allow to skip frames
    __traceback_hide__ = True
    if isinstance(context_or_env, Context):
        env = context_or_env.environment
        namespace = context_or_env.to_dict()
    else:
        env = context_or_env
        namespace = {}

    offset = '\n' * (lineno - 1)
    code = compile(offset + 'raise __exception_to_raise__',
                   filename or '<template>', 'exec')
    globals = {
        '__name__':                 filename,
        '__file__':                 filename,
        '__loader__':               TracebackLoader(env, source, filename),
        '__exception_to_raise__':   exception
    }
    try:
        exec code in globals, namespace
    except:
        return sys.exc_info()


def translate_exception(template, exc_type, exc_value, traceback, context):
    """
    Translate an exception and return the new traceback.
    """
    error_line = traceback.tb_lineno
    for code_line, tmpl_filename, tmpl_line in template._debug_info[::-1]:
        if code_line <= error_line:
            break
    else:
        # no debug symbol found. give up
        return traceback

    return fake_template_exception(exc_value, tmpl_filename, tmpl_line,
                                   template._source, context)[2]


def raise_syntax_error(exception, env, source=None):
    """
    This method raises an exception that includes more debugging
    informations so that debugging works better. Unlike
    `translate_exception` this method raises the exception with
    the traceback.
    """
    exc_info = fake_template_exception(exception, exception.filename,
                                       exception.lineno, source, env)
    raise exc_info[0], exc_info[1], exc_info[2]


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
            if len(node.args) in (1, 3):
                args = []
                for arg in node.args:
                    if not arg.__class__ is Const:
                        break
                    args.append(arg.value)
                else:
                    if len(args) == 1:
                        singular = args[0]
                        plural = None
                    else:
                        singular, plural, _ = args
                    result.append((node.lineno, singular, plural))
        todo.extend(node.getChildNodes())
    result.sort(lambda a, b: cmp(a[0], b[0]))
    return result


class TracebackLoader(object):
    """
    Fake importer that just returns the source of a template.
    """

    def __init__(self, environment, source, filename):
        self.loader = environment.loader
        self.source = source
        self.filename = filename

    def get_source(self, impname):
        if self.source is not None:
            return self.source
        elif self.loader is not None:
            try:
                return self.loader.get_source(self.filename)
            except TemplateNotFound:
                pass
        return ''


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

        # use a deque here if possible
        if deque is not None:
            self._queue = deque()
            self._popleft = self._queue.popleft
        # python2.3/2.4, just use a list
        else:
            self._queue = []
            pop = self._queue.pop
            self._popleft = lambda: pop(0)

        # alias all queue methods for faster lookup
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
        try:
            self._queue.clear()
        except AttributeError:
            del self._queue[:]

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
        try:
            return reversed(self._queue)
        except NameError:
            return iter(self._queue[::-1])

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
