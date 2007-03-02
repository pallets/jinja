# -*- coding: utf-8 -*-
"""
    jinja.loaders
    ~~~~~~~~~~~~~

    Jinja loader classes.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import codecs
from os import path
from jinja.parser import Parser
from jinja.translators.python import PythonTranslator
from jinja.exceptions import TemplateNotFound


__all__ = ['FileSystemLoader']


def get_template_filename(searchpath, name):
    """
    Return the filesystem filename wanted.
    """
    return path.join(searchpath, path.sep.join([p for p in name.split('/')
                     if p and p[0] != '.']))


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
    ``use_cache``       Set this to ``True`` to enable memory caching.
                        This is usually a good idea in production mode,
                        but disable it during development since it won't
                        reload template changes automatically.
                        This only works in persistent environments like
                        FastCGI.
    ``cache_size``      Number of template instance you want to cache.
                        Defaults to ``40``.
    =================== =================================================
    """

    def __init__(self, searchpath, use_cache=False, cache_size=40):
        self.searchpath = searchpath
        self.use_cache = use_cache
        self.cache_size = cache_size
        self.cache = {}

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

    def parse(self, environment, name, parent):
        source = self.get_source(environment, name, parent)
        return Parser(environment, source, name).parse()

    def load(self, environment, name, translator):
        if self.use_cache:
            key = (name, translator)
            if key in self.cache:
                return self.cache[key]
            if len(self.cache) >= self.cache_size:
                self.cache.clear()
        rv = translator.process(environment, self.parse(environment, name, None))
        if self.use_cache:
            self.cache[key] = rv
        return rv
