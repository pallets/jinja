# -*- coding: utf-8 -*-
"""
    jinja.filters
    ~~~~~~~~~~~~~

    Bundled jinja filters.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from random import choice
from operator import itemgetter
from urllib import urlencode, quote
from jinja.utils import urlize, escape, reversed, sorted, groupby
from jinja.datastructure import TemplateData
from jinja.exceptions import FilterArgumentError


_striptags_re = re.compile(r'(<!--.*?-->|<[^>]+>)')


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


def simplefilter(f):
    """
    Decorator for simplifying filters. Filter arguments are passed
    to the decorated function without environment and context. The
    source value is the first argument. (like stringfilter but
    without unicode conversion)
    """
    def decorator(*args):
        def wrapped(env, context, value):
            return f(value, *args)
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
        raise FilterArgumentError('the replace filter requires '
                                  'string replacement arguments')
    if count is None:
        return s.replace(old, new)
    if not isinstance(count, (int, long)):
        raise FilterArgumentError('the count parameter of the '
                                   'replace filter requires '
                                   'an integer')
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


def do_escape(attribute=False):
    """
    XML escape ``&``, ``<``, and ``>`` in a string of data. If the
    optional parameter is `true` this filter will also convert
    ``"`` to ``&quot;``. This filter is just used if the environment
    was configured with disabled `auto_escape`.

    This method will have no effect it the value is already escaped.
    """
    #: because filters are cached we can make a local alias to
    #: speed things up a bit
    e = escape
    def wrapped(env, context, s):
        if isinstance(s, TemplateData):
            return s
        elif hasattr(s, '__html__'):
            return s.__html__()
        #: small speedup, do not convert to unicode if we already
        #: have an unicode object.
        if s.__class__ is not unicode:
            s = env.to_unicode(s)
        return e(s, attribute)
    return wrapped


def do_xmlattr(autospace=False):
    """
    Create an SGML/XML attribute string based on the items in a dict.
    All values that are neither `none` nor `undefined` are automatically
    escaped:

    .. sourcecode:: html+jinja

        <ul{{ {'class': 'my_list', 'missing': None,
                'id': 'list-%d'|format(variable)}|xmlattr }}>
        ...
        </ul>

    Results in something like this:

    .. sourcecode:: html

        <ul class="my_list" id="list-42">
        ...
        </ul>

    As you can see it automatically prepends a space in front of the item
    if the filter returned something. You can disable this by passing
    `false` as only argument to the filter.

    *New in Jinja 1.1*
    """
    e = escape
    def wrapped(env, context, d):
        if not hasattr(d, 'iteritems'):
            raise TypeError('a dict is required')
        result = []
        for key, value in d.iteritems():
            if value not in (None, env.undefined_singleton):
                result.append(u'%s="%s"' % (
                    e(env.to_unicode(key)),
                    e(env.to_unicode(value), True)
                ))
        rv = u' '.join(result)
        if autospace:
            rv = ' ' + rv
        return rv
    return wrapped


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
        if (boolean and not value) or value in (env.undefined_singleton, None):
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
            return env.undefined_singleton
    return wrapped


def do_last():
    """
    Return the last item of a sequence.
    """
    def wrapped(env, context, seq):
        try:
            return iter(reversed(seq)).next()
        except StopIteration:
            return env.undefined_singleton
    return wrapped


def do_random():
    """
    Return a random item from the sequence.
    """
    def wrapped(env, context, seq):
        try:
            return choice(seq)
        except IndexError:
            return env.undefined_singleton
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
    return textile(s.encode('utf-8')).decode('utf-8')
do_textile = stringfilter(do_textile)


def do_markdown(s):
    """
    Parse the string using markdown.

    requires the `Python-markdown`_ library.

    .. _Python-markdown: http://www.freewisdom.org/projects/python-markdown/
    """
    from markdown import markdown
    return markdown(s.encode('utf-8')).decode('utf-8')
do_markdown = stringfilter(do_markdown)


def do_rst(s):
    """
    Parse the string using the reStructuredText parser from the
    docutils package.

    requires `docutils`_.

    .. _docutils: http://docutils.sourceforge.net/
    """
    from docutils.core import publish_parts
    parts = publish_parts(source=s, writer_name='html4css1')
    return parts['fragment']
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
    like in python. Use `|dformat` for that.
    """
    def wrapped(env, context, value):
        return env.to_unicode(value) % args
    return wrapped


def do_dformat(d):
    """
    Apply python mapping string formatting on an object:

    .. sourcecode:: jinja

        {{ "Hello %(username)s!"|dformat({'username': 'John Doe'}) }}
            -> Hello John Doe!

    This is useful when adding variables to translateable
    string expressions.

    *New in Jinja 1.1*
    """
    if not isinstance(d, dict):
        raise FilterArgumentError('dict required')
    def wrapped(env, context, value):
        return env.to_unicode(value) % d
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
    if not isinstance(name, basestring):
        raise FilterArgumentError('You can only capture into variables')
    def wrapped(env, context, value):
        context[name] = value
        if clean:
            return TemplateData()
        return value
    return wrapped


def do_striptags(value):
    """
    Strip SGML/XML tags and replace adjacent whitespace by one space.

    *new in Jinja 1.1*
    """
    return ' '.join(_striptags_re.sub('', value).split())
do_striptags = stringfilter(do_striptags)


def do_slice(slices, fill_with=None):
    """
    Slice an iterator and return a list of lists containing
    those items. Useful if you want to create a div containing
    three div tags that represent columns:

    .. sourcecode:: html+jinja

        <div class="columwrapper">
          {%- for column in items|slice(3) %}
            <ul class="column-{{ loop.index }}">
            {%- for item in column %}
              <li>{{ item }}</li>
            {%- endfor %}
            </ul>
          {%- endfor %}
        </div>

    If you pass it a second argument it's used to fill missing
    values on the last iteration.

    *new in Jinja 1.1*
    """
    def wrapped(env, context, value):
        result = []
        seq = list(value)
        length = len(seq)
        items_per_slice = length // slices
        slices_with_extra = length % slices
        offset = 0
        for slice_number in xrange(slices):
            start = offset + slice_number * items_per_slice
            if slice_number < slices_with_extra:
                offset += 1
            end = offset + (slice_number + 1) * items_per_slice
            tmp = seq[start:end]
            if fill_with is not None and slice_number >= slices_with_extra:
                tmp.append(fill_with)
            result.append(tmp)
        return result
    return wrapped


def do_batch(linecount, fill_with=None):
    """
    A filter that batches items. It works pretty much like `slice`
    just the other way round. It returns a list of lists with the
    given number of items. If you provide a second parameter this
    is used to fill missing items. See this example:

    .. sourcecode:: html+jinja

        <table>
        {%- for row in items|batch(3, '&nbsp;') %}
          <tr>
          {%- for column in row %}
            <tr>{{ column }}</td>
          {%- endfor %}
          </tr>
        {%- endfor %}
        </table>

    *new in Jinja 1.1*
    """
    def wrapped(env, context, value):
        result = []
        tmp = []
        for item in value:
            if len(tmp) == linecount:
                result.append(tmp)
                tmp = []
            tmp.append(item)
        if tmp:
            if fill_with is not None and len(tmp) < linecount:
                tmp += [fill_with] * (linecount - len(tmp))
            result.append(tmp)
        return result
    return wrapped


def do_sum():
    """
    Sum up the given sequence of numbers.

    *new in Jinja 1.1*
    """
    def wrapped(env, context, value):
        return sum(value)
    return wrapped


def do_abs():
    """
    Return the absolute value of a number.

    *new in Jinja 1.1*
    """
    def wrapped(env, context, value):
        return abs(value)
    return wrapped


def do_round(precision=0, method='common'):
    """
    Round the number to a given precision. The first
    parameter specifies the precision (default is ``0``), the
    second the rounding method:

    - ``'common'`` rounds either up or down
    - ``'ceil'`` always rounds up
    - ``'floor'`` always rounds down

    If you don't specify a method ``'common'`` is used.

    .. sourcecode:: jinja

        {{ 42.55|round }}
            -> 43
        {{ 42.55|round(1, 'floor') }}
            -> 42.5

    *new in Jinja 1.1*
    """
    if not method in ('common', 'ceil', 'floor'):
        raise FilterArgumentError('method must be common, ceil or floor')
    if precision < 0:
        raise FilterArgumentError('precision must be a postive integer '
                                  'or zero.')
    def wrapped(env, context, value):
        if method == 'common':
            return round(value, precision)
        import math
        func = getattr(math, method)
        if precision:
            return func(value * 10 * precision) / (10 * precision)
        else:
            return func(value)
    return wrapped


def do_sort(reverse=False):
    """
    Sort a sequence. Per default it sorts ascending, if you pass it
    `True` as first argument it will reverse the sorting.

    *new in Jinja 1.1*
    """
    def wrapped(env, context, value):
        return sorted(value, reverse=reverse)
    return wrapped


def do_groupby(attribute):
    """
    Group a sequence of objects by a common attribute.

    If you for example have a list of dicts or objects that represent persons
    with `gender`, `first_name` and `last_name` attributes and you want to
    group all users by genders you can do something like the following
    snippet:

    .. sourcecode:: html+jinja

        <ul>
        {% for group in persons|groupby('gender') %}
            <li>{{ group.grouper }}<ul>
            {% for person in group.list %}
                <li>{{ person.first_name }} {{ person.last_name }}</li>
            {% endfor %}</ul></li>
        {% endfor %}
        </ul>

    As you can see the item we're grouping by is stored in the `grouper`
    attribute and the `list` contains all the objects that have this grouper
    in common.

    *New in Jinja 1.2*
    """
    def wrapped(env, context, value):
        expr = lambda x: env.get_attribute(x, attribute)
        return sorted([{
            'grouper':  a,
            'list':     list(b)
        } for a, b in groupby(sorted(value, key=expr), expr)],
            key=itemgetter('grouper'))
    return wrapped


FILTERS = {
    'replace':              do_replace,
    'upper':                do_upper,
    'lower':                do_lower,
    'escape':               do_escape,
    'e':                    do_escape,
    'xmlattr':              do_xmlattr,
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
    'dformat':              do_dformat,
    'capture':              do_capture,
    'trim':                 do_trim,
    'striptags':            do_striptags,
    'slice':                do_slice,
    'batch':                do_batch,
    'sum':                  do_sum,
    'abs':                  do_abs,
    'round':                do_round,
    'sort':                 do_sort,
    'groupby':              do_groupby
}
