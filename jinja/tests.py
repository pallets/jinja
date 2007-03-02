# -*- coding: utf-8 -*-
"""
    jinja.tests
    ~~~~~~~~~~~

    Jinja test functions. Used with the "is" operator.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja.datastructure import Undefined


number_re = re.compile(r'^-?\d+(\.\d+)$')

regex_type = type(number_re)


def test_odd():
    """
    Return true if the variable is odd.
    """
    return lambda e, c, v: v % 2 == 1


def test_even():
    """
    Return true of the variable is even.
    """
    return lambda e, c, v: v % 2 == 0


def test_defined():
    """
    Return true if the variable is defined:

    .. sourcecode:: jinja

        {% if variable is defined %}
            value of variable: {{ variable }}
        {% else %}
            variable is not defined
        {% endif %}

    See also the ``default`` filter.
    """
    return lambda e, c, v: v is not Undefined


def test_lower():
    """
    Return true if the variable is lowercase.
    """
    return lambda e, c, v: isinstance(v, basestring) and v.islower()


def test_upper():
    """
    Return true if the variable is uppercase.
    """
    return lambda e, c, v: isinstance(v, basestring) and v.isupper()


def test_numeric():
    """
    Return true if the variable is numeric.
    """
    return lambda e, c, v: isinstance(v, (int, long, float)) or (
                           isinstance(v, basestring) and
                               number_re.match(v) is not None)


def test_sequence():
    """
    Return true if the variable is a sequence. Sequences are variables
    that are iterable.
    """
    def wrapped(environment, context, value):
        try:
            len(value)
            value.__getitem__
        except:
            return False
        return True
    return wrapped


def test_matching(regex):
    """
    Test if the variable matches the regular expression
    given. If the regular expression is a string additional
    slashes are automatically added, if it's a compiled regex
    it's used without any modifications:

    .. sourcecode:: jinja

        {% if var is matching('\d+$') %}
            var looks like a number
        {% else %}
            var doesn't really look like a number
        {% endif %}
    """
    if isinstance(regex, unicode):
        regex = re.compile(regex.encode('unicode-escape'), re.U)
    elif isinstance(regex, unicode):
        regex = re.compile(regex.encode('string-escape'))
    elif type(regex) is not regex_type:
        regex = None
    def wrapped(environment, context, value):
        if regex is None:
            return False
        else:
            return regex.match(value)
    return wrapped

TESTS = {
    'odd':              test_odd,
    'even':             test_even,
    'defined':          test_defined,
    'lower':            test_lower,
    'upper':            test_upper,
    'numeric':          test_numeric,
    'sequence':         test_sequence,
    'matching':         test_matching
}
