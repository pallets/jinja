# -*- coding: utf-8 -*-
"""
    jinja2.ext.entrypoints
    ~~~~~~~~~~~~~~~~~~~~~~

    These Jinja extensions advertise the Jinja2 engine by way of entry points.
    It was intended for consumption by the TurboGears and ToscaWidgets
    frameworks but can be reused by others.

    This module was lifted from Mako ext/turbogears.py
    Copyright (C) 2006-2012 the Mako authors and contributors.

    :copyright: (c) 2012 by the Jinja Team.
    :license: BSD.
"""

import re
import inspect

from jinja2 import Template
from jinja2 import Environment, PackageLoader


class EPPlugin(object):
    """ Plugin for delivering Jinja2 as an entry point """

    def __init__(self, extra_vars_func=None, options=None, extension='html'):
        self.extra_vars_func = extra_vars_func
        self.extension = extension
        if not options:
            options = {}

        # Pull the options out and initialize the lookup
        lookup_options = {}
        for k, v in options.iteritems():
            if k.startswith('jinja2.'):
                lookup_options[k[7:]] = v
            elif k in ['directories', 'filesystem_checks', 'module_directory']:
                lookup_options[k] = v

        self.lookup_options = lookup_options

    def load_template(self, templatename, template_string=None):
        """Loads a template from a file or a string"""
        if template_string is not None:
            return Template(template_string)

        toks = templatename.split('.')
        package, folder, tname = '.'.join(toks[:-2]), toks[-2], toks[-1]
        env = Environment(loader=PackageLoader(package, folder))
        return env.get_template(tname + '.' + self.extension)

    def render(self, info, format="html", fragment=False, template=None):
        if isinstance(template, basestring):
            template = self.load_template(template)

        # Load extra vars func if provided
        if self.extra_vars_func:
            info.update(self.extra_vars_func())

        return template.render(**info)
