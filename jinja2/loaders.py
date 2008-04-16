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


class BaseLoader(object):
    """Baseclass for all loaders."""

    def get_source(self, environment, template):
        raise TemplateNotFound()

    def load(self, environment, name, globals=None):
        source, filename = self.get_source(environment, name)
        code = environment.compile(source, name, filename, globals=globals)
        return Template(environment, code, globals or {})


class FileSystemLoader(BaseLoader):

    def __init__(self, path, encoding='utf-8'):
        self.path = path
        self.encoding = encoding

    def get_source(self, environment, template):
        pieces = []
        for piece in template.split('/'):
            if piece == '..':
                raise TemplateNotFound()
            elif piece != '.':
                pieces.append(piece)
        filename = path.join(self.path, *pieces)
        if not path.isfile(filename):
            raise TemplateNotFound(template)
        f = file(filename)
        try:
            return f.read().decode(self.encoding), filename
        finally:
            f.close()


class DictLoader(BaseLoader):

    def __init__(self, mapping):
        self.mapping = mapping

    def get_source(self, environment, template):
        if template in self.mapping:
            return self.mapping[template], template
        raise TemplateNotFound(template)
