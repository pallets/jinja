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


__all__ = ['FileSystemLoader']


def get_template_filename(searchpath, name):
    """
    Return the filesystem filename wanted.
    """
    return path.join(searchpath, path.sep.join([p for p in name.split('/')
                     if p and p[0] != '.']))


def get_template_cachename(cachepath, name):
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


class FileSystemLoader(object):
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
        self.use_memcache = use_memcache
        if use_memcache:
            self.memcache = CacheDict(memcache_size)
        else:
            self.memcache = None
        self.cache_folder = cache_folder
        self.auto_reload = auto_reload
        self._times = {}
        self._lock = Lock()

    def get_source(self, environment, name, parent):
        """
        Get the source code of a template.
        """
        filename = get_template_filename(self.searchpath, name)
        if path.exists(filename):
            f = codecs.open(filename, 'r', environment.template_charset)
            try:
                return f.read()
            finally:
                f.close()
        else:
            raise TemplateNotFound(name)

    def parse(self, environment, name, parent):
        """
        Load and parse a template
        """
        source = self.get_source(environment, name, parent)
        return Parser(environment, source, name).parse()

    def load(self, environment, name, translator):
        """
        Load, parse and translate a template.
        """
        self._lock.acquire()
        try:
            # caching is only possible for the python translator. skip
            # all other translators
            if translator is PythonTranslator:
                tmpl = None

                # auto reload enabled? check for the last change of the template
                if self.auto_reload:
                    last_change = path.getmtime(get_template_filename(self.searchpath, name))
                else:
                    last_change = None

                # check if we have something in the memory cache and the
                # memory cache is enabled.
                if self.use_memcache and name in self.memcache:
                    tmpl = self.memcache[name]
                    if last_change is not None and last_change > self._times[name]:
                        tmpl = None

                # if diskcache is enabled look for an already compiled template
                if self.cache_folder is not None:
                    cache_filename = get_template_cachename(self.cache_folder, name)

                    # there is a up to date compiled template
                    if tmpl is not None and last_change is None:
                        try:
                            cache_time = path.getmtime(cache_filename)
                        except OSError:
                            cache_time = 0
                        if last_change >= cache_time:
                            f = file(cache_filename, 'rb')
                            try:
                                tmpl = Template.load(environment, f)
                            finally:
                                f.close()

                    # no template so far, parse, translate and compile it
                    elif tmpl is None:
                        tmpl = translator.process(environment, self.parse(environment, name, None))

                    # save the compiled template
                    f = file(cache_filename, 'wb')
                    try:
                        tmpl.dump(f)
                    finally:
                        f.close()

                # if memcaching is enabled push the template
                if tmpl is not None:
                    if self.use_memcache:
                        self._times[name] = time.time()
                        self.memcache[name] = tmpl
                    return tmpl

            # if we reach this point we don't have caching enabled or translate
            # to something else than python
            return translator.process(environment, self.parse(environment, name, None))
        finally:
            self._lock.release()
