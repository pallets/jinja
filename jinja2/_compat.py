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


if not PY2:
    unichr = chr
    range_type = range
    text_type = str
    string_types = (str,)

    _iterkeys = 'keys'
    _itervalues = 'values'
    _iteritems = 'items'

    from io import BytesIO, StringIO
    NativeStringIO = StringIO

    ifilter = filter
    imap = map
    izip = zip

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    Iterator = object

    class UnicodeMixin(object):
        __slots__ = ()
        def __str__(self):
            return self.__unicode__()
else:
    text_type = unicode
    unichr = unichr
    string_types = (str, unicode)

    _iterkeys = 'iterkeys'
    _itervalues = 'itervalues'
    _iteritems = 'iteritems'

    from itertools import imap, izip, ifilter
    range_type = xrange

    from cStringIO import StringIO as BytesIO
    from StringIO import StringIO
    NativeStringIO = BytesIO

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    class UnicodeMixin(object):
        __slots__ = ()
        def __str__(self):
            return self.__unicode__().encode('utf-8')

    class Iterator(object):
        __slots__ = ()
        def next(self):
            return self.__next__()

try:
    next = next
except NameError:
    def next(it):
        return it.next()


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta('NewBase', bases, {})

def iterkeys(d, **kw):
    return iter(getattr(d, _iterkeys)(**kw))

def itervalues(d, **kw):
    return iter(getattr(d, _itervalues)(**kw))

def iteritems(d, **kw):
    return iter(getattr(d, _iteritems)(**kw))

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from collections import Mapping as mapping_types
except ImportError:
    import UserDict
    mapping_types = (UserDict.UserDict, UserDict.DictMixin, dict)


# common types.  These do exist in the special types module too which however
# does not exist in IronPython out of the box.  Also that way we don't have
# to deal with implementation specific stuff here
class _C(object):
    def method(self): pass
def _func():
    yield None
function_type = type(_func)
generator_type = type(_func())
method_type = type(_C().method)
code_type = type(_C.method.__code__)
try:
    raise TypeError()
except TypeError:
    _tb = sys.exc_info()[2]
    traceback_type = type(_tb)
    frame_type = type(_tb.tb_frame)
del _C, _tb, _func
