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


def escape(obj, attribute=False):
    """HTML escape an object."""
    if hasattr(obj, '__html__'):
        return obj.__html__()
    return unicode(obj) \
        .replace('&', '&amp;') \
        .replace('>', '&gt;') \
        .replace('<', '&lt;') \
        .replace('"', '&quot;')


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
    '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$' %  (
        '|'.join([re.escape(p) for p in ('(', '<', '&lt;')]),
        '|'.join([re.escape(p) for p in ('.', ',', ')', '>', '\n', '&gt;')])
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
