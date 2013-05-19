# -*- coding: utf-8 -*-
"""
    jinja2._compat
    ~~~~~~~~~~~~~~

    Some py2/py3 compatibility support that is not yet available in
    "six" 1.3.0.  Generally all uses of six should go through this module
    so that we have one central place to remove stuff from when we
    eventually drop 2.x.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import six
import sys

PY3 = six.PY3

# https://bitbucket.org/gutworth/six/issue/25/add-unichr
try:
    unichr = unichr  # py2
except NameError:
    unichr = chr  # py3

range_type = six.moves.xrange
next = six.advance_iterator
imap = six.moves.map
izip = six.moves.zip
text_type = six.text_type
string_types = six.string_types

iteritems = six.iteritems

if six.PY3:
    from io import BytesIO, StringIO
    NativeStringIO = StringIO
else:
    from cStringIO import StringIO as BytesIO
    from StringIO import StringIO
    NativeStringIO = BytesIO

try:
    import cPickle as pickle
except ImportError:
    import pickle

ifilter = six.moves.filter
reraise = six.reraise
Iterator = six.Iterator
with_metaclass = six.with_metaclass

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
