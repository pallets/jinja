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
    {{ var is odd }}

    Return True if the variable is odd.
    """
    return lambda e, c, v: v % 2 == 1


def test_even():
    """
    {{ var is even }}

    Return True of the variable is even.
    """
    return lambda e, c, v: v % 2 == 0


def test_defined():
    """
    {{ var is defined }}

    Return True if the variable is defined.
    """
    return lambda e, c, v: v is not Undefined


def test_lower():
    """
    {{ var is lower }}

    Return True if the variable is lowercase.
    """
    return lambda e, c, v: isinstance(v, basestring) and v.islower()


def test_upper():
    """
    {{ var is upper }}

    Return True if the variable is uppercase.
    """
    return lambda e, c, v: isinstance(v, basestring) and v.isupper()


def test_numeric():
    """
    {{ var is numeric }}

    Return True if the variable is numeric.
    """
    return lambda e, c, v: isinstance(v, (int, long, float)) or (
                           isinstance(v, basestring) and
                               number_re.match(v) is not None)


def test_sequence():
    """
    {{ var is sequence }}

    Return True if the variable is a sequence.
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
    {{ var is matching('\d+$') }}

    Test if the variable matches the regular expression
    given. If the regular expression is a string additional
    slashes are automatically added, if it's a compiled regex
    it's used without any modifications.
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
