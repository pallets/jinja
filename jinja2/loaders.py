# -*- coding: utf-8 -*-
"""
    jinja2.loaders
    ~~~~~~~~~~~~~~

    Jinja loader classes.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from os import path
from jinja2.exceptions import TemplateNotFound
from jinja2.environment import template_from_code
from jinja2.utils import LRUCache


def split_template_path(template):
    """Split a path into segments and perform a sanity check.  If it detects
    '..' in the path it will raise a `TemplateNotFound` error.
    """
    pieces = []
    for piece in template.split('/'):
        if path.sep in piece \
           or (path.altsep and path.altsep in piece) or \
           piece == path.pardir:
            raise TemplateNotFound(template)
        elif piece != '.':
            pieces.append(piece)
    return pieces


class BaseLoader(object):
    """Baseclass for all loaders.  Subclass this and override `get_source` to
    implement a custom loading mechanism.

    The environment provides a `get_template` method that will automatically
    call the loader bound to an environment.
    """

    def __init__(self, cache_size=50, auto_reload=True):
        if cache_size == 0:
            self.cache = None
        elif cache_size < 0:
            self.cache = {}
        else:
            self.cache = LRUCache(cache_size)
        self.auto_reload = auto_reload

    def get_source(self, environment, template):
        """Get the template source, filename and reload helper for a template.
        It's passed the environment and template name and has to return a
        tuple in the form ``(source, filename, uptodate)`` or raise a
        `TemplateNotFound` error if it can't locate the template.

        The source part of the returned tuple must be the source of the
        template as unicode string or a ASCII bytestring.  The filename should
        be the name of the file on the filesystem if it was loaded from there,
        otherwise `None`.  The filename is used by python for the tracebacks
        if no loader extension is used.

        The last item in the tuple is the `uptodate` function.  If auto
        reloading is enabled it's always called to check if the template
        changed.  No arguments are passed so the function must store the
        old state somewhere (for example in a closure).  If it returns `False`
        the template will be reloaded.
        """
        raise TemplateNotFound(template)

    def load(self, environment, name, globals=None):
        """Loads a template.  This method should not be overriden by
        subclasses unless `get_source` doesn't provide enough flexibility.
        """
        if globals is None:
            globals = {}

        if self.cache is not None:
            template = self.cache.get(name)
            if template is not None and (not self.auto_reload or \
                                         template.is_up_to_date):
                return template

        source, filename, uptodate = self.get_source(environment, name)
        code = environment.compile(source, name, filename, globals)
        template = template_from_code(environment, code, globals, uptodate)
        if self.cache is not None:
            self.cache[name] = template
        return template


class FileSystemLoader(BaseLoader):
    """Loads templates from the file system."""

    def __init__(self, searchpath, encoding='utf-8', cache_size=50,
                 auto_reload=True):
        BaseLoader.__init__(self, cache_size, auto_reload)
        if isinstance(searchpath, basestring):
            searchpath = [searchpath]
        self.searchpath = searchpath
        self.encoding = encoding

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        for searchpath in self.searchpath:
            filename = path.join(searchpath, *pieces)
            if not path.isfile(filename):
                continue
            f = file(filename)
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()
            old = path.getmtime(filename)
            return contents, filename, lambda: path.getmtime(filename) != old
        raise TemplateNotFound(template)


class PackageLoader(BaseLoader):
    """Load templates from python eggs."""

    def __init__(self, package_name, package_path, charset='utf-8',
                 cache_size=50, auto_reload=True):
        BaseLoader.__init__(self, cache_size, auto_reload)
        import pkg_resources
        self._pkg = pkg_resources
        self.package_name = package_name
        self.package_path = package_path

    def get_source(self, environment, template):
        pieces = split_template_path(template)
        path = '/'.join((self.package_path,) + tuple(pieces))
        if not self._pkg.resource_exists(self.package_name, path):
            raise TemplateNotFound(template)
        return self._pkg.resource_string(self.package_name, path), None, None


class DictLoader(BaseLoader):
    """Loads a template from a python dict.  Used for unittests mostly."""

    def __init__(self, mapping, cache_size=50):
        BaseLoader.__init__(self, cache_size, False)
        self.mapping = mapping

    def get_source(self, environment, template):
        if template in self.mapping:
            return self.mapping[template], None, None
        raise TemplateNotFound(template)


class FunctionLoader(BaseLoader):
    """A loader that is passed a function which does the loading.  The
    function becomes the name of the template passed and has to return either
    an unicode string with the template source, a tuple in the form ``(source,
    filename, uptodatefunc)`` or `None` if the template does not exist.
    """

    def __init__(self, load_func, cache_size=50, auto_reload=True):
        BaseLoader.__init__(self, cache_size, auto_reload)
        self.load_func = load_func

    def get_source(self, environment, template):
        rv = self.load_func(template)
        if rv is None:
            raise TemplateNotFound(template)
        elif isinstance(rv, basestring):
            return rv, None, None
        return rv


class PrefixLoader(BaseLoader):
    """A loader that is passed a dict of loaders where each loader is bound
    to a prefix.  The caching is independent of the actual loaders so the
    per loader cache settings are ignored.  The prefix is delimited from the
    template by a slash.
    """

    def __init__(self, mapping, delimiter='/', cache_size=50,
                 auto_reload=True):
        BaseLoader.__init__(self, cache_size, auto_reload)
        self.mapping = mapping
        self.delimiter = delimiter

    def get_source(self, environment, template):
        try:
            prefix, template = template.split(self.delimiter, 1)
            loader = self.mapping[prefix]
        except (ValueError, KeyError):
            raise TemplateNotFound(template)
        return loader.get_source(environment, template)


class ChoiceLoader(BaseLoader):
    """This loader works like the `PrefixLoader` just that no prefix is
    specified.  If a template could not be found by one loader the next one
    is tried.  Like for the `PrefixLoader` the cache settings of the actual
    loaders don't matter as the choice loader does the caching.
    """

    def __init__(self, loaders, cache_size=50, auto_reload=True):
        BaseLoader.__init__(self, cache_size, auto_reload)
        self.loaders = loaders

    def get_source(self, environment, template):
        for loader in self.loaders:
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(template)
