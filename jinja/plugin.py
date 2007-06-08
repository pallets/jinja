# -*- coding: utf-8 -*-
"""
    jinja.plugin
    ~~~~~~~~~~~~

    Support for the `GeneralTemplateInterface`__ and the Buffet interface.

    Do not use this module on your own. We don't recommend those interfaces!
    If you are able to, you should really use Jinja without those abstraction
    layers.

    __ http://trac.pocoo.org/wiki/GeneralTemplateInterface

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.environment import Environment
from jinja.loaders import FunctionLoader, FileSystemLoader, PackageLoader
from jinja.exceptions import TemplateNotFound


class BuffetPlugin(object):
    """
    Implements the Jinja buffet plugin. Well. It works for pylons and should
    work for TurboGears too if their plugin system would work.
    """

    def __init__(self, extra_vars_func=None, options=None):
        if 'jinja.environment' in options:
            self.env = options['jinja.environment']
        else:
            opt = {}
            for key, value in options.iteritems():
                if key.startswith('jinja.') and key != 'jinja.extension':
                    opt[key[6:]] = value
            loader_func = opt.pop('loader_func', None)
            getmtime_func = opt.pop('getmtime_func', None)
            use_memcache = opt.pop('use_memcache', False)
            memcache_size = opt.pop('memcache_size', 40)
            cache_folder = opt.pop('cache_folder', None)
            auto_reload = opt.pop('auto_reload', True)
            if 'searchpath' in opt:
                opt['loader'] = FileSystemLoader(opt.pop('searchpath'),
                                                 use_memcache, memcache_size,
                                                 cache_folder, auto_reload)
            elif 'package' in opt:
                opt['loader'] = PackageLoader(opt.pop('package'),
                                              opt.pop('package_path', ''),
                                              use_memcache, memcache_size,
                                              cache_folder, auto_reload)
            elif loader_func is not None:
                opt['loader'] = FunctionLoader(loader_func, getmtime_func,
                                               use_memcache, memcache_size,
                                               cache_folder, auto_reload)
            self.env = Environment(**opt)

        self.extra_vars_func = extra_vars_func
        self.extension = options.pop('jinja.extension', 'html')

    def load_template(self, templatename, template_string=None):
        if template_string is not None:
            return self.env.from_string(template_string)
        if templatename.startswith('!'):
            jinja_name = templatename[1:]
        else:
            jinja_name = templatename.replace('.', '/') + '.' + self.extension
        return self.env.get_template(jinja_name)

    def render(self, info, format='html', fragment=False, template=None):
        if isinstance(template, basestring):
            template = self.load_template(template)
        if self.extra_vars_func:
            info.update(self.extra_vars_func())
        return template.render(info)


def jinja_plugin_factory(options):
    """
    Basic implementation of the `GeneralTemplateInterface`.

    Supports ``loader_func`` and ``getmtime_func``, as well as
    string and file loading but ignores ``mode`` since it's a
    text based template engine.

    All options passed to this function are forwarded to the
    jinja environment. Exceptions are the following keys:

    =================== =================================================
    ``environment``     If this is provided it must be the only
                        configuration value and it's used as jinja
                        environment.
    ``searchpath``      If provided a new file system loader with this
                        search path is instanciated.
    ``package``         Name of the python package containing the
                        templates. If this and ``package_path`` is
                        defined a `PackageLoader` is used.
    ``package_path``    Path to the templates inside of a package.
    ``loader_func``     Function that takes the name of the template to
                        load. If it returns a string or unicode object
                        it's used to load a template. If the return
                        value is None it's considered missing.
    ``getmtime_func``   Function used to check if templates requires
                        reloading. Has to return the UNIX timestamp of
                        the last template change or 0 if this template
                        does not exist or requires updates at any cost.
    ``use_memcache``    Set this to ``True`` to enable memory caching.
                        This is usually a good idea in production mode,
                        but disable it during development since it won't
                        reload template changes automatically.
                        This only works in persistent environments like
                        FastCGI.
    ``memcache_size``   Number of template instance you want to cache.
                        Defaults to ``40``.
    ``cache_folder``    Set this to an existing directory to enable
                        caching of templates on the file system. Note
                        that this only affects templates transformed
                        into python code. Default is ``None`` which means
                        that caching is disabled.
    ``auto_reload``     Set this to `False` for a slightly better
                        performance. In that case of `getmtime_func`
                        not being provided this won't have an effect.
    =================== =================================================
    """
    if 'environment' in options:
        env = options['environment']
        if not len(options) == 1:
            raise TypeError('if environment provided no other '
                            'arguments are allowed')
    else:
        loader_func = options.pop('loader_func', None)
        getmtime_func = options.pop('getmtime_func', None)
        use_memcache = options.pop('use_memcache', False)
        memcache_size = options.pop('memcache_size', 40)
        cache_folder = options.pop('cache_folder', None)
        auto_reload = options.pop('auto_reload', True)
        if 'searchpath' in options:
            options['loader'] = FileSystemLoader(options.pop('searchpath'),
                                                 use_memcache, memcache_size,
                                                 cache_folder, auto_reload)
        elif 'package' in options:
            options['loader'] = PackageLoader(options.pop('package'),
                                              options.pop('package_path', ''),
                                              use_memcache, memcache_size,
                                              cache_folder, auto_reload)
        elif loader_func is not None:
            options['loader'] = FunctionLoader(loader_func, getmtime_func,
                                               use_memcache, memcache_size,
                                               cache_folder, auto_reload)
        env = Environment(**options)

    def render_function(template, values, options):
        if options.get('is_string'):
            tmpl = env.from_string(template)
        else:
            try:
                tmpl = env.get_template(template)
            except TemplateNotFound:
                return
        return tmpl.render(**values)

    return render_function
