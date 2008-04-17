# -*- coding: utf-8 -*-
"""
    jinja2.utils
    ~~~~~~~~~~~~

    Utility functions.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
import string
from functools import update_wrapper
from itertools import imap


def escape(obj, attribute=False):
    """HTML escape an object."""
    if obj is None:
        return u''
    elif hasattr(obj, '__html__'):
        return obj.__html__()
    return Markup(unicode(obj)
        .replace('&', '&amp;')
        .replace('>', '&gt;')
        .replace('<', '&lt;')
        .replace('"', '&quot;')
    )


def soft_unicode(s):
    """Make a string unicode if it isn't already.  That way a markup
    string is not converted back to unicode.
    """
    if not isinstance(s, unicode):
        s = unicode(s)
    return s


def pformat(obj, verbose=False):
    """
    Prettyprint an object.  Either use the `pretty` library or the
    builtin `pprint`.
    """
    try:
        from pretty import pretty
        return pretty(obj, verbose=verbose)
    except ImportError:
        from pprint import pformat
        return pformat(obj)


_word_split_re = re.compile(r'(\s+)')

_punctuation_re = re.compile(
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' % (
        '|'.join(imap(re.escape, ('(', '<', '&lt;'))),
        '|'.join(imap(re.escape, ('.', ',', ')', '>', '\n', '&gt;')))
    )
)

_simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')


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


class Markup(unicode):
    """Marks a string as being safe for inclusion in HTML/XML output without
    needing to be escaped.  This implements the `__html__` interface a couple
    of frameworks and web applications use.

    The `escape` function returns markup objects so that double escaping can't
    happen.  If you want to use autoescaping in Jinja just set the finalizer
    of the environment to `escape`.
    """

    __slots__ = ()

    def __html__(self):
        return self

    def __add__(self, other):
        if hasattr(other, '__html__') or isinstance(other, basestring):
            return self.__class__(unicode(self) + unicode(escape(other)))
        return NotImplemented

    def __radd__(self, other):
        if hasattr(other, '__html__') or isinstance(other, basestring):
            return self.__class__(unicode(escape(other)) + unicode(self))
        return NotImplemented

    def __mul__(self, num):
        if not isinstance(num, (int, long)):
            return NotImplemented
        return self.__class__(unicode.__mul__(self, num))
    __rmul__ = __mul__

    def __mod__(self, arg):
        if isinstance(arg, tuple):
            arg = tuple(imap(_MarkupEscapeHelper, arg))
        else:
            arg = _MarkupEscapeHelper(arg)
        return self.__class__(unicode.__mod__(self, arg))

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            unicode.__repr__(self)
        )

    def join(self, seq):
        return self.__class__(unicode.join(self, imap(escape, seq)))

    def split(self, *args, **kwargs):
        return map(self.__class__, unicode.split(self, *args, **kwargs))

    def rsplit(self, *args, **kwargs):
        return map(self.__class__, unicode.rsplit(self, *args, **kwargs))

    def splitlines(self, *args, **kwargs):
        return map(self.__class__, unicode.splitlines(self, *args, **kwargs))

    def make_wrapper(name):
        orig = getattr(unicode, name)
        def func(self, *args, **kwargs):
            args = list(args)
            for idx, arg in enumerate(args):
                if hasattr(arg, '__html__') or isinstance(arg, basestring):
                    args[idx] = escape(arg)
            for name, arg in kwargs.iteritems():
                if hasattr(arg, '__html__') or isinstance(arg, basestring):
                    kwargs[name] = escape(arg)
            return self.__class__(orig(self, *args, **kwargs))
        return update_wrapper(func, orig, ('__name__', '__doc__'))
    for method in '__getitem__', '__getslice__', 'capitalize', \
                  'title', 'lower', 'upper', 'replace', 'ljust', \
                  'rjust', 'lstrip', 'rstrip', 'partition', 'center', \
                  'strip', 'translate', 'expandtabs', 'rpartition', \
                  'swapcase', 'zfill':
        locals()[method] = make_wrapper(method)
    del method, make_wrapper


class _MarkupEscapeHelper(object):
    """Helper for Markup.__mod__"""

    def __init__(self, obj):
        self.obj = obj

    __getitem__ = lambda s, x: _MarkupEscapeHelper(s.obj[x])
    __unicode__ = lambda s: unicode(escape(s.obj))
    __str__ = lambda s: str(escape(s.obj))
    __repr__ = lambda s: str(repr(escape(s.obj)))
    __int__ = lambda s: int(s.obj)
    __float__ = lambda s: float(s.obj)
