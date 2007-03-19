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
from jinja.utils import escape, urlize
from jinja.datastructure import Undefined
from jinja.exceptions import FilterArgumentError


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
    if not isinstance(old, basestring) or \
       not isinstance(new, basestring):
        raise FilterArgumentException('the replace filter requires '
                                      'string replacement arguments')
    elif not isinstance(count, (int, long)):
        raise FilterArgumentException('the count parameter of the '
                                      'replace filter requires '
                                      'an integer')
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


def do_dictsort(case_sensitive=False, by='key'):
    """
    Sort a dict and yield (key, value) pairs. Because python dicts are
    unsorted you may want to use this function to order them by either
    key or value:

    .. sourcecode:: jinja

        {% for item in mydict|dictsort %}
            sort the dict by key, case insensitive

        {% for item in mydict|dicsort(true) %}
            sort the dict by key, case sensitive

        {% for item in mydict|dictsort(false, 'value') %}
            sort the dict by key, case insensitive, sorted
            normally and ordered by value.
    """
    if by == 'key':
        pos = 0
    elif by == 'value':
        pos = 1
    else:
        raise FilterArgumentError('You can only sort by either '
                                  '"key" or "value"')
    def sort_func(value, env):
        if isinstance(value, basestring):
            value = env.to_unicode(value)
            if not case_sensitive:
                value = value.lower()
        return value

    def wrapped(env, context, value):
        items = value.items()
        items.sort(lambda a, b: cmp(sort_func(a[pos], env),
                                    sort_func(b[pos], env)))
        return items
    return wrapped


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
        if (boolean and not value) or value in (Undefined, None):
            return default_value
        return value
    return wrapped


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


def do_filesizeformat():
    """
    Format the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB, 102
    bytes, etc).
    """
    def wrapped(env, context, value):
        # fail silently
        try:
            bytes = float(value)
        except TypeError:
            bytes = 0

        if bytes < 1024:
            return "%d Byte%s" % (bytes, bytes != 1 and 's' or '')
        elif bytes < 1024 * 1024:
            return "%.1f KB" % (bytes / 1024)
        elif bytes < 1024 * 1024 * 1024:
            return "%.1f MB" % (bytes / (1024 * 1024))
        return "%.1f GB" % (bytes / (1024 * 1024 * 1024))
    return wrapped


def do_pprint():
    """
    Pretty print a variable. Useful for debugging.
    """
    def wrapped(env, context, value):
        from pprint import pformat
        return pformat(value)
    return wrapped


def do_urlize(value, trim_url_limit=None, nofollow=False):
    """
    Converts URLs in plain text into clickable links.

    If you pass the filter an additional integer it will shorten the urls
    to that number. Also a third argument exists that makes the urls
    "nofollow":

    .. sourcecode:: jinja

        {{ mytext|urlize(40, True) }}
            links are shortened to 40 chars and defined with rel="nofollow"
    """
    return urlize(value, trim_url_limit, nofollow)
do_urlize = stringfilter(do_urlize)


def do_indent(s, width=4, indentfirst=False):
    """
    {{ s|indent[ width[ indentfirst[ usetab]]] }}

    Return a copy of the passed string, each line indented by
    4 spaces. The first line is not indented. If you want to
    change the number of spaces or indent the first line too
    you can pass additional parameters to the filter:

    .. sourcecode:: jinja

        {{ mytext|indent(2, True) }}
            indent by two spaces and indent the first line too.
    """
    indention = ' ' * width
    if indentfirst:
        return u'\n'.join([indention + line for line in s.splitlines()])
    return s.replace('\n', '\n' + indention)
do_indent = stringfilter(do_indent)


def do_truncate(s, length=255, killwords=False, end='...'):
    """
    Return a truncated copy of the string. The length is specified
    with the first parameter which defaults to ``255``. If the second
    parameter is ``true`` the filter will cut the text at length. Otherwise
    it will try to save the last word. If the text was in fact
    truncated it will append an ellipsis sign (``"..."``). If you want a
    different ellipsis sign than ``"..."`` you can specify it using the
    third parameter.

    .. sourcecode jinja::

        {{ mytext|truncate(300, false, '&raquo;') }}
            truncate mytext to 300 chars, don't split up words, use a
            right pointing double arrow as ellipsis sign.
    """
    if len(s) <= length:
        return s
    elif killwords:
        return s[:length] + end
    words = s.split(' ')
    result = []
    m = 0
    for word in words:
        m += len(word) + 1
        if m > length:
            break
        result.append(word)
    result.append(end)
    return u' '.join(result)
do_truncate = stringfilter(do_truncate)


def do_wordwrap(s, pos=79, hard=False):
    """
    Return a copy of the string passed to the filter wrapped after
    ``79`` characters. You can override this default using the first
    parameter. If you set the second parameter to `true` Jinja will
    also split words apart (usually a bad idea because it makes
    reading hard).
    """
    if len(s) < pos:
        return s
    if hard:
        return u'\n'.join([s[idx:idx + pos] for idx in
                          xrange(0, len(s), pos)])
    # code from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
    return reduce(lambda line, word, pos=pos: u'%s%s%s' %
                  (line, u' \n'[(len(line)-line.rfind('\n') - 1 +
                                len(word.split('\n', 1)[0]) >= pos)],
                   word), s.split(' '))
do_wordwrap = stringfilter(do_wordwrap)


def do_wordcount(s):
    """
    Count the words in that string.
    """
    return len([x for x in s.split() if x])
do_wordcount = stringfilter(do_wordcount)


def do_textile(s):
    """
    Prase the string using textile.

    requires the `PyTextile`_ library.

    .. _PyTextile: http://dealmeida.net/projects/textile/
    """
    from textile import textile
    return textile(s)
do_textile = stringfilter(do_textile)


def do_markdown(s):
    """
    Parse the string using markdown.

    requires the `Python-markdown`_ library.

    .. _Python-markdown: http://www.freewisdom.org/projects/python-markdown/
    """
    from markdown import markdown
    return markdown(s)
do_markdown = stringfilter(do_markdown)


def do_rst(s):
    """
    Parse the string using the reStructuredText parser from the
    docutils package.

    requires `docutils`_.

    .. _docutils: from http://docutils.sourceforge.net/
    """
    try:
        from docutils.core import publish_parts
        parts = publish_parts(source=s, writer_name='html4css1')
        return parts['fragment']
    except:
        return s
do_rst = stringfilter(do_rst)


def do_int(default=0):
    """
    Convert the value into an integer. If the
    conversion doesn't work it will return ``0``. You can
    override this default using the first parameter.
    """
    def wrapped(env, context, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default
    return wrapped


def do_float(default=0.0):
    """
    Convert the value into a floating point number. If the
    conversion doesn't work it will return ``0.0``. You can
    override this default using the first parameter.
    """
    def wrapped(env, context, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    return wrapped


def do_string():
    """
    Convert the value into an string.
    """
    return lambda e, c, v: e.to_unicode(v)


def do_format(*args):
    """
    Apply python string formatting on an object:

    .. sourcecode:: jinja

        {{ "%s - %s"|format("Hello?", "Foo!") }}
            -> Hello? - Foo!

    Note that you cannot use the mapping syntax (``%(name)s``)
    like in python.
    """
    def wrapped(env, context, value):
        return env.to_unicode(value) % args
    return wrapped


def do_trim(value):
    """
    Strip leading and trailing whitespace.
    """
    return value.strip()
do_trim = stringfilter(do_trim)


def do_capture(name='captured', clean=False):
    """
    Store the value in a variable called ``captured`` or a variable
    with the name provided. Useful for filter blocks:

    .. sourcecode:: jinja

        {% filter capture('foo') %}
            ...
        {% endfilter %}
        {{ foo }}

    This will output "..." two times. One time from the filter block
    and one time from the variable. If you don't want the filter to
    output something you can use it in `clean` mode:

    .. sourcecode:: jinja

        {% filter capture('foo', True) %}
            ...
        {% endfilter %}
        {{ foo }}
    """
    if not isinstance(name, unicode):
        raise FilterArgumentError('You can only capture into variables')
    def wrapped(env, context, value):
        context[name] = value
        if clean:
            return Undefined
        return value
    return wrapped


FILTERS = {
    'replace':              do_replace,
    'upper':                do_upper,
    'lower':                do_lower,
    'escape':               do_escape,
    'e':                    do_escape,
    'capitalize':           do_capitalize,
    'title':                do_title,
    'default':              do_default,
    'join':                 do_join,
    'count':                do_count,
    'dictsort':             do_dictsort,
    'length':               do_count,
    'reverse':              do_reverse,
    'center':               do_center,
    'title':                do_title,
    'capitalize':           do_capitalize,
    'first':                do_first,
    'last':                 do_last,
    'random':               do_random,
    'urlencode':            do_urlencode,
    'jsonencode':           do_jsonencode,
    'filesizeformat':       do_filesizeformat,
    'pprint':               do_pprint,
    'indent':               do_indent,
    'truncate':             do_truncate,
    'wordwrap':             do_wordwrap,
    'wordcount':            do_wordcount,
    'textile':              do_textile,
    'markdown':             do_markdown,
    'rst':                  do_rst,
    'int':                  do_int,
    'float':                do_float,
    'string':               do_string,
    'urlize':               do_urlize,
    'format':               do_format,
    'capture':              do_capture,
    'trim':                 do_trim
}
