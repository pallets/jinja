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

# https://bitbucket.org/gutworth/six/issue/25/add-unichr
try:
    unichr = unichr  # py2
except NameError:
    unichr = chr  # py3

range_type = six.moves.xrange
next = six.advance_iterator
imap = six.moves.map
