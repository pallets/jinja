# -*- coding: utf-8 -*-
"""
    jinja2.defaults
    ~~~~~~~~~~~~~~~

    Jinja default filters and tags.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.filters import FILTERS as DEFAULT_FILTERS
from jinja2.tests import TESTS as DEFAULT_TESTS
from jinja2.utils import generate_lorem_ipsum


BLOCK_START_STRING = '{%'
BLOCK_END_STRING = '%}'
VARIABLE_START_STRING = '{{'
VARIABLE_END_STRING = '}}'
COMMENT_START_STRING = '{#'
COMMENT_END_STRING = '#}'
LINE_STATEMENT_PREFIX = None


DEFAULT_NAMESPACE = {
    'range':        xrange,
    'dict':         lambda **kw: kw,
    'lipsum':       generate_lorem_ipsum,
    'void':         lambda *a: u''
}


# export all constants
__all__ = tuple(x for x in locals() if x.isupper())
