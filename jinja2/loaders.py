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
from jinja2.environment import Template
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
    """
    Baseclass for all loaders.  Subclass this and override `get_source` to
    implement a custom loading mechanism.

    The environment provides a `get_template` method that will automatically
    call the loader bound to an environment.
    """

    def __init__(self, cache_size=50, auto_reload=True):
        if cache_size > 0:
            self.cache = LRUCache(cache_size)
        else:
            self.cache = None
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
        template = Template(environment, code, globals, uptodate)
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
        path = '/'.join(split_template_path(template))
        if not self._pkg.resource_exists(self.package_name, path):
            raise TemplateNotFound(template)
        return self._pkg.resource_string(self.package_name, path), None, None


class DictLoader(BaseLoader):
    """Loads a template from a python dict.  Used for unittests mostly."""

    def __init__(self, mapping):
        self.mapping = mapping

    def get_source(self, environment, template):
        if template in self.mapping:
            return self.mapping[template], None, None
        raise TemplateNotFound(template)
