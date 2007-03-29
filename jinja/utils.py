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
from jinja.exceptions import SecurityException

try:
    from collections import deque
except ImportError:
    deque = None

#: number of maximal range items
MAX_RANGE = 1000000

_debug_info_re = re.compile(r'^\s*\# DEBUG\(filename=(.*?), lineno=(.*?)\)$')

_integer_re = re.compile('^(\d+)$')

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


# python2.4 and lower has a bug regarding joining of broken generators
if sys.version_info < (2, 5):
    capture_generator = lambda gen: u''.join(tuple(gen))

# this should be faster and used in python2.5 and higher
else:
    capture_generator = u''.join


def buffereater(f):
    """
    Used by the python translator to capture output of substreams.
    (macros, filter sections etc)
    """
    def wrapped(*args, **kwargs):
        return TemplateData(capture_generator(f(*args, **kwargs)))
    return wrapped


def fake_template_exception(exception, filename, lineno, context_or_env):
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
    code = compile(offset + 'raise __exception_to_raise__', filename, 'exec')
    globals = {
        '__name__':                 filename,
        '__file__':                 filename,
        '__loader__':               TracebackLoader(env, filename),
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
    sourcelines = template.translated_source.splitlines()
    startpos = traceback.tb_lineno - 1
    filename = None
    # looks like we loaded the template from string. we cannot
    # do anything here.
    if startpos > len(sourcelines):
        return traceback

    while startpos > 0:
        m = _debug_info_re.search(sourcelines[startpos])
        if m is not None:
            filename, lineno = m.groups()
            if filename == 'None':
                filename = None
            if lineno != 'None':
                lineno = int(lineno)
            break
        startpos -= 1

    # no traceback information found, reraise unchanged
    if not filename:
        return traceback

    return fake_template_exception(exc_value, filename,
                                   lineno, context)[2]


def raise_syntax_error(exception, env):
    """
    This method raises an exception that includes more debugging
    informations so that debugging works better. Unlike
    `translate_exception` this method raises the exception with
    the traceback.
    """
    exc_info = fake_template_exception(exception, exception.filename,
                                       exception.lineno, env)
    raise exc_info[0], exc_info[1], exc_info[2]


def collect_translations(ast):
    """
    Collect all translatable strings for the given ast.
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

    def __init__(self, environment, filename):
        self.loader = environment.loader
        self.filename = filename

    def get_source(self, impname):
        return self.loader.get_source(self.filename)


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
        # python2.3, just use a list
        else:
            self._queue = []
            pop = self._queue.pop
            self._popleft = lambda: pop(0)

        # alias all queue methods for faster lookup
        self._pop = self._queue.pop
        self._remove = self._queue.remove
        self._append = self._queue.append

    def copy(self):
        rv = CacheDict(self.capacity)
        rv._mapping.update(self._mapping)
        rv._queue = self._queue[:]
        return rv

    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]
        self[key] = default
        return default

    def clear(self):
        self._mapping.clear()
        try:
            self._queue.clear()
        except AttributeError:
            del self._queue[:]

    def __contains__(self, key):
        return key in self._mapping

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._mapping
        )

    def __getitem__(self, key):
        rv = self._mapping[key]
        if self._queue[-1] != key:
            self._remove(key)
            self._append(key)
        return rv

    def __setitem__(self, key, value):
        if key in self._mapping:
            self._remove(key)
        elif len(self._mapping) == self.capacity:
            del self._mapping[self._popleft()]
        self._append(key)
        self._mapping[key] = value

    def __delitem__(self, key):
        del self._mapping[key]
        self._remove(key)

    def __iter__(self):
        try:
            return reversed(self._queue)
        except NameError:
            return iter(self._queue[::-1])

    def __reversed__(self):
        return iter(self._queue)

    __copy__ = copy
