# -*- coding: utf-8 -*-
"""
    jinja.filters
    ~~~~~~~~~~~~~

    Bundled jinja filters.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


def stringfilter(f):
    """
    Decorator for filters that just work on unicode objects.
    """
    def decorator(*args):
        def wrapped(env, context, value):
            args = list(args)
            for idx, var in enumerate(args):
                if isinstance(var, str):
                    args[idx] = env.to_unicode(var)
            return f(env.to_unicode(value), *args)
        return wrapped
    return decorator


def do_replace(s, old, new, count=None):
    """
    {{ s|replace(old, new, count=None) }}

    Return a copy of s with all occurrences of substring
    old replaced by new. If the optional argument count is
    given, only the first count occurrences are replaced.
    """
    if count is None:
        return s.replace(old, new)
    return s.replace(old, new, count)


def do_upper(s):
    """
    {{ s|upper }}

    Return a copy of s converted to uppercase.
    """
    return s.upper()


def do_lower(s):
    """
    {{ s|lower }}

    Return a copy of s converted to lowercase.
    """
    return s.lower()


def do_escape(s, attribute=False):
    """
    {{ s|escape(attribute) }}

    XML escape &, <, and > in a string of data. If attribute is
    True it also converts ``"`` to ``&quot;``
    """
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if attribute:
        s = s.replace('"', "&quot;")
    return s


def do_addslashes(s):
    """
    {{ s|addslashes }}

    Adds slashes to s.
    """
    return s.encode('utf-8').encode('string-escape').decode('utf-8')


def do_capitalize(s):
    """
    {{ s|capitalize }}

    Return a copy of the string s with only its first character
    capitalized.
    """
    return s.capitalize()


def do_title(s):
    """
    {{ s|title }}

    Return a titlecased version of s, i.e. words start with uppercase
    characters, all remaining cased characters have lowercase.
    """
    return s.title()


def do_default(default_value=u''):
    """
    {{ s|default(default_value='') }}

    In case of s isn't set or True default will return default_value
    which is '' per default.
    """
    return lambda e, c, v: v or default_value


def do_join(d=u''):
    """
    {{ sequence|join(d='') }}

    Return a string which is the concatenation of the strings in the
    sequence. The separator between elements is d which is an empty
    string per default.
    """
    def wrapped(env, context, value):
        d = env.to_unicode(d)
        return d.join([env.to_unicode(x) for x in value])
    return wrapped


def do_count():
    """
    {{ var|count }}

    Return the length of var. In case if getting an integer or float
    it will convert it into a string an return the length of the new
    string.
    If the object doesn't provide a __len__ function it will return
    zero.st(value)
        l.reverse()
        return 
    """
    def wrapped(env, context, value):
        try:
            if type(value) in (int, float, long):
                return len(str(var))
            return len(var)
        except TypeError:
            return 0
    return wrapped


def do_odd():
    """
    {{ var|odd }}

    Return true if the variable is odd.
    """
    return lambda e, c, v: v % 2 == 1


def do_even():
    """
    {{ var|even }}

    Return true of the variable is even.
    """
    return lambda e, c, v: v % 2 == 0


def do_reversed():
    """
    {{ var|reversed }}

    Return a reversed list of the iterable filtered.
    """
    def wrapped(env, context, value):
        try:
            return value[::-1]
        except:
            l = list(value)
            l.reverse()
            return l
    return wrapped


FILTERS = {
    'replace':              do_replace,
    'upper':                do_upper,
    'lower':                do_lower,
    'escape':               do_escape,
    'e':                    do_escape,
    'addslashes':           do_addslashes,
    'capitalize':           do_capitalize,
    'title':                do_title,
    'default':              do_default,
    'join':                 do_join,
    'count':                do_count,
    'odd':                  do_odd,
    'even':                 do_even,
    'reversed':             do_reversed
}
