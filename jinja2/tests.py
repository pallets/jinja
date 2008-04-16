# -*- coding: utf-8 -*-
"""
    jinja.tests
    ~~~~~~~~~~~

    Jinja test functions. Used with the "is" operator.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja2.runtime import Undefined


number_re = re.compile(r'^-?\d+(\.\d+)?$')
regex_type = type(number_re)


def test_odd(value):
    """Return true if the variable is odd."""
    return value % 2 == 1


def test_even(value):
    """Return true of the variable is even."""
    return value % 2 == 0


def test_defined(value):
    """Return true if the variable is defined:

    .. sourcecode:: jinja

        {% if variable is defined %}
            value of variable: {{ variable }}
        {% else %}
            variable is not defined
        {% endif %}

    See also the ``default`` filter.
    """
    return not isinstance(value, Undefined)


def test_lower(value):
    """Return true if the variable is lowercase."""
    return unicode(value).islower()


def test_upper(value):
    """Return true if the variable is uppercase."""
    return unicode(value).isupper()


def test_numeric(value):
    """Return true if the variable is numeric."""
    return isinstance(value, (int, long, float)) or (
           isinstance(value, basestring) and
           number_re.match(value) is not None)


def test_sequence(value):
    """Return true if the variable is a sequence. Sequences are variables
    that are iterable.
    """
    try:
        len(value)
        value.__getitem__
    except:
        return False
    return True


def test_sameas(value, other):
    """Check if an object points to the same memory address than another
    object:

    .. sourcecode:: jinja

        {% if foo.attribute is sameas(false) %}
            the foo attribute really is the `False` singleton
        {% endif %}

    *New in Jinja 1.2*
    """
    return value is other


TESTS = {
    'odd':              test_odd,
    'even':             test_even,
    'defined':          test_defined,
    'lower':            test_lower,
    'upper':            test_upper,
    'numeric':          test_numeric,
    'sequence':         test_sequence,
    'sameas':           test_sameas
}
