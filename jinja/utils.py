# -*- coding: utf-8 -*-
"""
    jinja.utils
    ~~~~~~~~~~~

    Utility functions.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja.datastructure import safe_types


_escape_pairs = {
    '&':            '&amp;',
    '<':            '&lt;',
    '>':            '&gt;',
    '"':            '&quot;'
}

_escape_res = (
    re.compile('(&|<|>|")'),
    re.compile('(&|<|>)')
)

def escape(x, attribute=False):
    """
    Escape an object x which is converted to unicode first.
    """
    if type(x) in safe_types:
        return x
    return _escape_res[not attribute].sub(lambda m: _escape_pairs[m.group()],
                                          unicode(x))
