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


class ConfigurationError(Exception):
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
        self.extension = options.get('jinja.extension', JinjaPlugin.extension)
        if 'jinja.environment' in options:
            self.environment = options['jinja.environment']
        else:
            # this wonderful piece of code was brought to you by the turbogears
            # ppl who want to put template configuration stuff into goddamn
            # text/plain configuration files.
            if 'jinja.environment.loader' in options:
                loader = options['jinja.environment.loader']
            else:
                loadername = options.get('jinja.loader') or 'FileSystemLoader'
                if '.' in loadername:
                    p = loadername.rsplit('.', 1)
                    loadercls = getattr(__import__(p[0], '', '', ['']), p[1])
                else:
                    from jinja import loaders
                    loadercls = getattr(loaders, loadername)
                loaderoptions = {}
                for k, v in options.iteritems():
                    if k.startswith('jinja.loader.'):
                        loaderoptions[k[14:]] = v
                loader = loadercls(**loaderoptions)
            if 'jinja.environment.context_class' in options:
                context_class = options['jinja.environment.context_class']
            else:
                contextname = options.get('jinja.context_class') or \
                              'jinja.datastructure.Context'
                if '.' in contextname:
                    p = contextname.rsplit('.', 1)
                    context_class = getattr(__import__(p[0], '', '', ['']), p[1])
                else:
                    from jinja import Context as context_class
            self.environment = Environment(
                block_start_string=options.get('jinja.block_start_string', '{%'),
                block_end_string=options.get('jinja.block_end_string', '%}'),
                variable_start_string=options.get('jinja.variable_start_string', '{{'),
                variable_end_string=options.get('jinja.variable_end_string', '}}'),
                comment_start_string=options.get('jinja.comment_start_string', '{#'),
                comment_end_string=options.get('jinja.comment_end_string', '#}'),
                trim_blocks=str(options.get('jinja.trim_blocks')).lower() in
                                ('true', 'on', 'yes', '1'),
                template_charset=options.get('jinja.template_charset', 'utf-8'),
                charset=options.get('jinja.charset', 'utf-8'),
                namespace=options.get('jinja.namespace'),
                loader=loader,
                filters=options.get('jinja.filters'),
                tests=options.get('jinja.tests'),
                context_class=context_class
            )

    def load_template(self, templatename, template_string=None):
        """
        Find a template specified in python 'dot' notation, or load one from
        a string.
        """
        if template_string is not None:
            return self.environment.from_string(template_string)

        # Translate TG dot notation to normal / template path
        if '/' not in templatename and '.' not in templatename:
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
