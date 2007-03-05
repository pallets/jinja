# -*- coding: utf-8 -*-
"""
    jinja.utils
    ~~~~~~~~~~~

    Utility functions.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
from jinja.nodes import Trans
from jinja.datastructure import safe_types, Markup


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
    return Markup(_escape_res[not attribute].sub(lambda m:
                  _escape_pairs[m.group()], unicode(x)))



def find_translations(environment, source):
    """
    Find all translatable strings in a template and yield
    them as (lineno, singular, plural) tuples. If a plural
    section does not exist it will be None.
    """
    queue = [environment.parse(source)]
    while queue:
        node = queue.pop()
        if node.__class__ is Trans:
            yield node.lineno, node.singular, node.plural
        queue.extend(node.getChildNodes())
