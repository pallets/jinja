# -*- coding: utf-8 -*-
"""
    jinja.bakerplugin
    ~~~~~~~~~~~~~~~~~

    Provide a bridge to baker. Baker is used by some frameworks (namely
    CherryPy, TurboGears and Pylons) to load templates.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja import Environment


class ConfigurationError(ValueError):
    """
    Raised if an configuration error occoured.
    """


class JinjaPlugin(object):
    """
    Implementation of the Plugin API
    """
    extension = 'html'

    def __init__(self, extra_vars_func=None, options=None):
        self.get_extra_vars = extra_vars_func
        options = options or {}
        if 'jinja.environment' in options:
            self.environment = options['jinja.environment']
        elif 'jinja.init_callback' in options:
            name = options['jinja.init_callback']
            p = name.rsplit('.', 1)
            func = getattr(__import__(p[0], '', '', ['']), p[1])
            self.environment = func(options)
        else:
            raise ConfigurationError('no jinja environment defined')
        if 'jinja.extension' in options:
            self.extension = options['jinja.extension']

    def load_template(self, templatename, template_string=None):
        """
        Find a template specified in python 'dot' notation, or load one from
        a string.
        """
        if template_string is not None:
            return self.environment.from_string(template_string)

        # Translate TG dot notation to normal / template path
        if '/' not in templatename and '.' in templatename:
            templatename = '/' + templatename.replace('.', '/') + '.' + self.extension

        return self.environment.get_template(templatename)

    def render(self, info, format='html', fragment=False, template=None):
        """
        Render a template.
        """
        if isinstance(template, basestring):
            template = self.load_template(template)

        if self.get_extra_vars:
            info.update(self.get_extra_vars())

        return template.render(**info)
