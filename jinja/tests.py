# -*- coding: utf-8 -*-
"""
    jinja.tests
    ~~~~~~~~~~~

    Jinja test functions. Used with the "is" operator.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re


number_re = re.compile(r'^-?\d+(\.\d+)?$')
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
    return lambda e, c, v: v is not e.undefined_singleton


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
    r"""
    Test if the variable matches the regular expression given. Note that
    you have to escape special chars using *two* backslashes, these are
    *not* raw strings.

    .. sourcecode:: jinja

        {% if var is matching('^\\d+$') %}
            var looks like a number
        {% else %}
            var doesn't really look like a number
        {% endif %}
    """
    if isinstance(regex, unicode):
        regex = re.compile(regex, re.U)
    elif isinstance(regex, str):
        regex = re.compile(regex)
    elif type(regex) is not regex_type:
        regex = None
    def wrapped(environment, context, value):
        if regex is None:
            return False
        return regex.search(value) is not None
    return wrapped


def test_sameas(other):
    """
    Check if an object points to the same memory address than another
    object:

    .. sourcecode:: jinja

        {% if foo.attribute is sameas(false) %}
            the foo attribute really is the `False` singleton
        {% endif %}

    *New in Jinja 1.2*
    """
    return lambda e, c, v: v is other


TESTS = {
    'odd':              test_odd,
    'even':             test_even,
    'defined':          test_defined,
    'lower':            test_lower,
    'upper':            test_upper,
    'numeric':          test_numeric,
    'sequence':         test_sequence,
    'matching':         test_matching,
    'sameas':           test_sameas
}
