# -*- coding: utf-8 -*-
"""
    jinja.loaders
    ~~~~~~~~~~~~~

    Jinja loader classes.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import codecs
import sha
import time
from os import path
from threading import Lock
from jinja.parser import Parser
from jinja.translators.python import PythonTranslator, Template
from jinja.exceptions import TemplateNotFound
from jinja.utils import CacheDict
try:
    from pkg_resources import resource_exists, resource_string, \
                              resource_filename
except ImportError:
    resource_exists = resource_string = resource_filename = None


__all__ = ['FileSystemLoader', 'PackageLoader', 'DictLoader', 'ChoiceLoader',
           'FunctionLoader']


def get_template_filename(searchpath, name):
    """
    Return the filesystem filename wanted.
    """
    return path.join(searchpath, path.sep.join([p for p in name.split('/')
                     if p and p[0] != '.']))


def get_cachename(cachepath, name):
    """
    Return the filename for a cached file.
    """
    return path.join(cachepath, 'jinja_%s.cache' %
                     sha.new('jinja(%s)tmpl' % name).hexdigest())


class LoaderWrapper(object):
    """
    Wraps a loader so that it's bound to an environment.
    """

    def __init__(self, environment, loader):
        self.environment = environment
        self.loader = loader
        if self.loader is None:
            self.get_source = self.parse = self.load = self._loader_missing
            self.available = False
        else:
            self.available = True

    def get_source(self, name, parent=None):
        """Retrieve the sourcecode of a template."""
        # just ascii chars are allowed as template names
        name = str(name)
        return self.loader.get_source(self.environment, name, parent)

    def parse(self, name, parent=None):
        """Retreive a template and parse it."""
        # just ascii chars are allowed as template names
        name = str(name)
        return self.loader.parse(self.environment, name, parent)

    def load(self, name, translator=PythonTranslator):
        """
        Translate a template and return it. This must not necesarily
        be a template class. The javascript translator for example
        will just output a string with the translated code.
        """
        # just ascii chars are allowed as template names
        name = str(name)
        return self.loader.load(self.environment, name, translator)

    def _loader_missing(self, *args, **kwargs):
        """Helper method that overrides all other methods if no
        loader is defined."""
        raise RuntimeError('no loader defined')

    def __nonzero__(self):
        return self.loader is not None


class BaseLoader(object):
    """
    Use this class to implement loaders.

    Just inherit from this class and implement a method called
    `get_source` with the signature (`environment`, `name`, `parent`)
    that returns sourcecode for the template.

    For more complex loaders you probably want to override `load` to
    or not use the `BaseLoader` at all.
    """

    def parse(self, environment, name, parent):
        """
        Load and parse a template
        """
        source = self.get_source(environment, name, parent)
        return Parser(environment, source, name).parse()

    def load(self, environment, name, translator):
        """
        Load and translate a template
        """
        ast = self.parse(environment, name, None)
        return translator.process(environment, ast)


class CachedLoaderMixin(object):
    """
    Mixin this class to implement simple memory and disk caching.
    """

    def __init__(self, use_memcache, cache_size, cache_folder, auto_reload):
        if use_memcache:
            self.__memcache = CacheDict(cache_size)
        else:
            self.__memcache = None
        self.__cache_folder = cache_folder
        if not hasattr(self, 'check_source_changed'):
            self.__auto_reload = False
        else:
            self.__auto_reload = auto_reload
        self.__times = {}
        self.__lock = Lock()

    def load(self, environment, name, translator):
        """
        Load and translate a template. First we check if there is a
        cached version of this template in the memory cache. If this is
        not the cache check for a compiled template in the disk cache
        folder. And if none of this is the case we translate the temlate
        using the `LoaderMixin.load` function, cache and return it.
        """
        self.__lock.acquire()
        try:
            # caching is only possible for the python translator. skip
            # all other translators
            if translator is PythonTranslator:
                tmpl = None

                # auto reload enabled? check for the last change of
                # the template
                if self.__auto_reload:
                    last_change = self.check_source_changed(environment, name)
                else:
                    last_change = None

                # check if we have something in the memory cache and the
                # memory cache is enabled.
                if self.__memcache is not None and name in self.__memcache:
                    tmpl = self.__memcache[name]
                    if last_change is not None and \
                       last_change > self.__times[name]:
                        tmpl = None

                # if diskcache is enabled look for an already compiled
                # template.
                if self.__cache_folder is not None:
                    cache_fn = get_cachename(self.__cache_folder, name)

                    # there is an up to date compiled template
                    if tmpl is not None and last_change is None:
                        try:
                            cache_time = path.getmtime(cache_fn)
                        except OSError:
                            cache_time = 0
                        if last_change >= cache_time:
                            f = file(cache_fn, 'rb')
                            try:
                                tmpl = Template.load(environment, f)
                            finally:
                                f.close()

                    # no template so far, parse, translate and compile it
                    elif tmpl is None:
                        tmpl = super(CachedLoaderMixin, self).load(
                                     environment, name, translator)

                    # save the compiled template
                    f = file(cache_fn, 'wb')
                    try:
                        tmpl.dump(f)
                    finally:
                        f.close()

                # if memcaching is enabled push the template
                if tmpl is not None:
                    if self.__memcache is not None:
                        self.__times[name] = time.time()
                        self.__memcache[name] = tmpl
                    return tmpl

            # if we reach this point we don't have caching enabled or translate
            # to something else than python
            return super(CachedLoaderMixin, self).load(
                         environment, name, translator)
        finally:
            self.__lock.release()


class FileSystemLoader(CachedLoaderMixin, BaseLoader):
    """
    Loads templates from the filesystem:

    .. sourcecode:: python

        from jinja import Environment, FileSystemLoader
        e = Environment(loader=FileSystemLoader('templates/'))

    You can pass the following keyword arguments to the loader on
    initialisation:

    =================== =================================================
    ``searchpath``      String with the path to the templates on the
                        filesystem.
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
                        performance. In that case Jinja won't check for
                        template changes on the filesystem.
    =================== =================================================
    """

    def __init__(self, searchpath, use_memcache=False, memcache_size=40,
                 cache_folder=None, auto_reload=True):
        self.searchpath = searchpath
        CachedLoaderMixin.__init__(self, use_memcache, memcache_size,
                                   cache_folder, auto_reload)

    def get_source(self, environment, name, parent):
        filename = get_template_filename(self.searchpath, name)
        if path.exists(filename):
            f = codecs.open(filename, 'r', environment.template_charset)
            try:
                return f.read()
            finally:
                f.close()
        else:
            raise TemplateNotFound(name)

    def check_source_changed(self, environment, name):
        filename = get_template_filename(self.searchpath, name)
        if path.exists(filename):
            return path.getmtime(filename)
        return 0


class PackageLoader(CachedLoaderMixin, BaseLoader):
    """
    Loads templates from python packages using setuptools.

    .. sourcecode:: python

        from jinja import Environment, PackageLoader
        e = Environment(loader=PackageLoader('yourapp', 'template/path'))

    You can pass the following keyword arguments to the loader on
    initialisation:

    =================== =================================================
    ``package_name``    Name of the package containing the templates.
    ``package_path``    Path of the templates inside the package.
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
                        performance. In that case Jinja won't check for
                        template changes on the filesystem. If the
                        templates are inside of an egg file this won't
                        have an effect.
    =================== =================================================
    """

    def __init__(self, package_name, package_path, use_memcache=False,
                 memcache_size=40, cache_folder=None, auto_reload=True):
        if resource_filename is None:
            raise ImportError('setuptools not found')
        self.package_name = package_name
        self.package_path = package_path
        # if we have an loader we probably retrieved it from an egg
        # file. In that case don't use the auto_reload!
        if auto_reload and getattr(__import__(package_name, '', '', ['']),
                                   '__loader__', None) is not None:
            auto_reload = False
        CachedLoaderMixin.__init__(self, use_memcache, memcache_size,
                                   cache_folder, auto_reload)

    def get_source(self, environment, name, parent):
        name = '/'.join([self.package_path] + [p for p in name.split('/')
                        if p != '..'])
        if not resource_exists(self.package_name, name):
            raise TemplateNotFound(name)
        contents = resource_string(self.package_name, name)
        return contents.decode(environment.template_charset)

    def check_source_changed(self, environment, name):
        fn = resource_filename(self.package_name, '/'.join([self.package_path] +
                               [p for p in name.split('/') if p and p[0] != '.']))
        if resource_exists(self.package_name, fn):
            return path.getmtime(fn)
        return 0


class FunctionLoader(CachedLoaderMixin, BaseLoader):
    """
    Loads templates by calling a function which has to return a string
    or `None` if an error occoured.

    .. sourcecode:: python

        from jinja import Environment, FunctionLoader

        def my_load_func(template_name):
            if template_name == 'foo':
                return '...'

        e = Environment(loader=FunctionLoader(my_load_func))

    Because the interface is limited there is no way to cache such
    templates. Usually you should try to use a loader with a more
    solid backend.

    You can pass the following keyword arguments to the loader on
    initialisation:

    =================== =================================================
    ``loader_func``     Function that takes the name of the template to
                        load. If it returns a string or unicode object
                        it's used to load a template. If the return
                        value is None it's considered missing.
    =================== =================================================
    """

    def __init__(self, loader_func):
        self.loader_func = loader_func

    def get_source(self, environment, name, parent):
        rv = self.loader_func(name)
        if rv is None:
            raise TemplateNotFound(name)
        if isinstance(rv, str):
            return rv.decode(environment.template_charset)
        return rv


class DictLoader(BaseLoader):
    """
    Load templates from a given dict:

    .. sourcecode:: python

        from jinja import Environment, DictLoader
        e = Environment(loader=DictLoader(dict(
            layout='...',
            index='{% extends 'layout' %}...'
        )))
    """

    def __init__(self, templates):
        self.templates = templates

    def get_source(self, environment, name, parent):
        if name in self.templates:
            return self.templates[name]
        raise TemplateNotFound(name)


class ChoiceLoader(object):
    """
    A loader that tries multiple loaders in the order they are given to
    the `ChoiceLoader`:

    .. sourcecode:: python

        from jinja import ChoiceLoader, FileSystemLoader
        loader1 = FileSystemLoader("templates1")
        loader2 = FileSystemLoader("templates2")
        loader = ChoiceLoader([loader1, loader2])
    """

    def __init__(self, loaders):
        self.loaders = list(loaders)

    def get_source(self, environment, name, parent):
        for loader in self.loaders:
            try:
                return loader.get_source(environment, name, parent)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(name)

    def parse(self, environment, name, parent):
        for loader in self.loaders:
            try:
                return loader.parse(environment, name, parent)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(name)

    def load(self, environment, name, translator):
        for loader in self.loaders:
            try:
                return loader.load(environment, name, translator)
            except TemplateNotFound:
                continue
        raise TemplateNotFound(name)
