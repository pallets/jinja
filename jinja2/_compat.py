# -*- coding: utf-8 -*-
"""
    jinja2._compat
    ~~~~~~~~~~~~~~

    Some py2/py3 compatibility support that is not yet available in
     "six" 1.3.0.
    There are bugs open for "six" for all this stuff, so we can remove it
    again from here as soon as we require a new enough "six" release.

    :copyright: Copyright 2013 by the Jinja team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# https://bitbucket.org/gutworth/six/issue/25/add-unichr
try:
    unichr = unichr  # py2
except NameError:
    unichr = chr  # py3

try:
    range_type = xrange
except NameError:
    range_type = range
