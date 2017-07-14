# -*- coding: utf-8 -*-
"""
    jinja2._compat
    ~~~~~~~~~~~~~~

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys

PY2 = sys.version_info[0] == 2
PYPY = hasattr(sys, 'pypy_translation_info')
_identity = lambda x: x  # noqa: E731


# avoid flake8 F821 undefined name 'long'
try:
    integer_types = (int, long)  # Python 2
except NameError:
    integer_types = (int, )      # Python 3

# avoid flake8 F821 undefined name 'unicode'
try:
    text_type = unicode  # Python 2
    string_types = (str, unicode)
except NameError:
    text_type = str      # Python 3
    string_types = (str, )

# avoid flake8 F821 undefined name 'xrange'
try:
    range_type = xrange  # Python 2
except NameError:
    range_type = range   # Python 3

if not PY2:
    unichr = chr

    iterkeys = lambda d: iter(d.keys())  # noqa: E731
    itervalues = lambda d: iter(d.values())  # noqa: E731
    iteritems = lambda d: iter(d.items())  # noqa: E731

    import pickle
    from io import BytesIO, StringIO
    NativeStringIO = StringIO

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    ifilter = filter
    imap = map
    izip = zip
    intern = sys.intern

    implements_iterator = _identity
    implements_to_string = _identity

else:
    unichr = unichr

    iterkeys = lambda d: d.iterkeys()  # noqa: E731
    itervalues = lambda d: d.itervalues()  # noqa: E731
    iteritems = lambda d: d.iteritems()  # noqa: E731

    import cPickle as pickle  # noqa :F401
    from cStringIO import StringIO as BytesIO, StringIO
    NativeStringIO = BytesIO

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    from itertools import imap, izip, ifilter  # noqa :F401
    intern = intern

    def implements_iterator(cls):
        cls.next = cls.__next__
        del cls.__next__
        return cls

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls


def encode_filename(filename):
    # avoid flake8 F821 undefined name 'unicode'
    try:               # Python 2
        if isinstance(filename, unicode):
            return filename.encode('utf-8')
    except NameError:  # Python 3
        pass
    return filename


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.
    class metaclass(type):
        def __new__(cls, name, this_bases, d):
            return meta(name, bases, d)
    return type.__new__(metaclass, 'temporary_class', (), {})


try:
    from urllib.parse import quote_from_bytes as url_quote  # noqa :F401
except ImportError:
    from urllib import quote as url_quote  # noqa :F401
