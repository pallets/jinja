# -*- coding: utf-8 -*-
"""
    jinja2.defaults
    ~~~~~~~~~~~~~~~

    Jinja default filters and tags.

    :copyright: 2007-2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.filters import FILTERS as DEFAULT_FILTERS
from jinja.tests import TESTS as DEFAULT_TESTS

DEFAULT_NAMESPACE = {
    'range': xrange
}
