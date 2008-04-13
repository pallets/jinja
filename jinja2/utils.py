# -*- coding: utf-8 -*-
"""
    jinja2.utils
    ~~~~~~~~~~~~

    Utility functions.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


def escape(obj, attribute=False):
    """HTML escape an object."""
    if hasattr(obj, '__html__'):
        return obj.__html__()
    return unicode(obj) \
        .replace('&', '&amp;') \
        .replace('>', '&gt;') \
        .replace('<', '&lt;') \
        .replace('"', '&quot;')


def pformat(obj, verbose=False):
    """
    Prettyprint an object.  Either use the `pretty` library or the
    builtin `pprint`.
    """
    try:
        from pretty import pretty
        return pretty(obj, verbose=verbose)
    except ImportError:
        from pprint import pformat
        return pformat(obj)
