# -*- coding: utf-8 -*-
"""
    Jinja Sandboxed Template Engine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.environment import Environment
from jinja.plugin import jinja_plugin_factory as template_plugin_factory
from jinja.loaders import *
from_string = Environment().from_string
