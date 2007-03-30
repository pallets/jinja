# -*- coding: utf-8 -*-
"""
    jinja.defaults
    ~~~~~~~~~~~~~~

    Jinja default filters and tags.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.filters import FILTERS as DEFAULT_FILTERS
from jinja.tests import TESTS as DEFAULT_TESTS
from jinja.utils import debug_context, safe_range, generate_lorem_ipsum


DEFAULT_NAMESPACE = {
    'range':                safe_range,
    'debug':                debug_context,
    'lipsum':               generate_lorem_ipsum
}
