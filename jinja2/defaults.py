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


DEFAULT_NAMESPACE = {
    'range':        xrange,
    'lipsum':       generate_lorem_ipsum
}
