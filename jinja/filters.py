# -*- coding: utf-8 -*-
"""
    jinja.filters
    ~~~~~~~~~~~~~

    Bundled jinja filters.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from random import choice
from urllib import urlencode, quote
from jinja.utils import escape
from jinja.datastructure import Undefined


try:
    _reversed = reversed
except NameError:
    # python2.3 compatibility hack for the do_reverse function
    def _reversed(seq):
        try:
            return seq[::-1]
        except:
            try:
                return list(seq)[::-1]
            except:
                raise TypeError('argument to _reversed must '
                                'be a sequence')


def stringfilter(f):
    """
    Decorator for filters that just work on unicode objects.
    """
    def decorator(*args):
        def wrapped(env, context, value):
            nargs = list(args)
            for idx, var in enumerate(nargs):
                if isinstance(var, str):
                    nargs[idx] = env.to_unicode(var)
            return f(env.to_unicode(value), *nargs)
        return wrapped
    try:
        decorator.__doc__ = f.__doc__
        decorator.__name__ = f.__name__
    except:
        pass
    return decorator


def do_replace(s, old, new, count=None):
    """
    Return a copy of the value with all occurrences of a substring
    replaced with a new one. The first argument is the substring
    that should be replaced, the second is the replacement string.
    If the optional third argument ``count`` is given, only the first
    ``count`` occurrences are replaced:

    .. sourcecode:: jinja

        {{ "Hello World"|replace("Hello", "Goodbye") }}
            -> Goodbye World

        {{ "aaaaargh"|replace("a", "d'oh, ", 2) }}
            -> d'oh, d'oh, aaargh
    """
    if count is None:
        return s.replace(old, new)
    return s.replace(old, new, count)
do_replace = stringfilter(do_replace)


def do_upper(s):
    """
    Convert a value to uppercase.
    """
    return s.upper()
do_upper = stringfilter(do_upper)


def do_lower(s):
    """
    Convert a value to lowercase.
    """
    return s.lower()
do_lower = stringfilter(do_lower)


def do_escape(s, attribute=False):
    """
    XML escape ``&``, ``<``, and ``>`` in a string of data. If the
    optional parameter is `true` this filter will also convert
    ``"`` to ``&quot;``. This filter is just used if the environment
    was configured with disabled `auto_escape`.

    This method will have no effect it the value is already escaped.
    """
    return escape(s, attribute)
do_escape = stringfilter(do_escape)


def do_addslashes(s):
    """
    Add backslashes in front of special characters to s. This method
    might be useful if you try to fill javascript strings. Also have
    a look at the `jsonencode` filter.
    """
    return s.encode('utf-8').encode('string-escape').decode('utf-8')
do_addslashes = stringfilter(do_addslashes)


def do_capitalize(s):
    """
    Capitalize a value. The first character will be uppercase, all others
    lowercase.
    """
    return s.capitalize()
do_capitalize = stringfilter(do_capitalize)


def do_title(s):
    """
    Return a titlecased version of the value. I.e. words will start with
    uppercase letters, all remaining characters are lowercase.
    """
    return s.title()
do_title = stringfilter(do_title)


def do_default(default_value=u'', boolean=False):
    """
    If the value is undefined it will return the passed default value,
    otherwise the value of the variable:

    .. sourcecode:: jinja

        {{ my_variable|default('my_variable is not defined') }}

    This will output the value of ``my_variable`` if the variable was
    defined, otherwise ``'my_variable is not defined'``. If you want
    to use default with variables that evaluate to false you have to
    set the second parameter to `true`:

    .. sourcecode:: jinja

        {{ ''|default('the string was empty', true) }}
    """
    def wrapped(env, context, value):
        if (boolean and not v) or v in (Undefined, None):
            return default_value
        return v
    return wrapped
do_default = stringfilter(do_default)


def do_join(d=u''):
    """
    Return a string which is the concatenation of the strings in the
    sequence. The separator between elements is an empty string per
    default, you can define ith with the optional parameter:

    .. sourcecode:: jinja

        {{ [1, 2, 3]|join('|') }}
            -> 1|2|3

        {{ [1, 2, 3]|join }}
            -> 123
    """
    def wrapped(env, context, value):
        return env.to_unicode(d).join([env.to_unicode(x) for x in value])
    return wrapped


def do_count():
    """
    Return the length of the value. In case if getting an integer or float
    it will convert it into a string an return the length of the new
    string. If the object has no length it will of corse return 0.
    """
    def wrapped(env, context, value):
        try:
            if type(value) in (int, float, long):
                return len(str(value))
            return len(value)
        except TypeError:
            return 0
    return wrapped


def do_reverse():
    """
    Return a reversed list of the sequence filtered. You can use this
    for example for reverse iteration:

    .. sourcecode:: jinja

        {% for item in seq|reverse %}
            {{ item|e }}
        {% endfor %}
    """
    def wrapped(env, context, value):
        try:
            return value[::-1]
        except:
            l = list(value)
            l.reverse()
            return l
    return wrapped


def do_center(value, width=80):
    """
    Centers the value in a field of a given width.
    """
    return value.center(width)
do_center = stringfilter(do_center)


def do_first():
    """
    Return the frist item of a sequence.
    """
    def wrapped(env, context, seq):
        try:
            return iter(seq).next()
        except StopIteration:
            return Undefined
    return wrapped


def do_last():
    """
    Return the last item of a sequence.
    """
    def wrapped(env, context, seq):
        try:
            return iter(_reversed(seq)).next()
        except (TypeError, StopIteration):
            return Undefined
    return wrapped


def do_random():
    """
    Return a random item from the sequence.
    """
    def wrapped(env, context, seq):
        try:
            return choice(seq)
        except:
            return Undefined
    return wrapped


def do_urlencode():
    """
    urlencode a string or directory.

    .. sourcecode:: jinja

        {{ {'foo': 'bar', 'blub': 'blah'}|urlencode }}
            -> foo=bar&blub=blah

        {{ 'Hello World' }}
            -> Hello%20World
    """
    def wrapped(env, context, value):
        if isinstance(value, dict):
            tmp = {}
            for key, value in value.iteritems():
                tmp[env.to_unicode(key)] = env.to_unicode(value)
            return urlencode(tmp)
        else:
            return quote(env.to_unicode(value))
    return wrapped


def do_jsonencode():
    """
    JSON dump a variable. just works if simplejson is installed.

    .. sourcecode:: jinja

        {{ 'Hello World'|jsonencode }}
            -> "Hello World"
    """
    global simplejson
    try:
        simplejson
    except NameError:
        import simplejson
    return lambda e, c, v: simplejson.dumps(v)


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
    'length':               do_count,
    'reverse':              do_reverse,
    'center':               do_center,
    'title':                do_title,
    'capitalize':           do_capitalize,
    'first':                do_first,
    'last':                 do_last,
    'random':               do_random,
    'urlencode':            do_urlencode,
    'jsonencode':           do_jsonencode
}
