# -*- coding: utf-8 -*-
"""
    jinja2.parser
    ~~~~~~~~~~~~~

    Implements the template parser.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja import nodes
from jinja.exceptions import TemplateSyntaxError


__all__ = ['Parser']


class Parser(object):
    """
    The template parser class.

    Transforms sourcecode into an abstract syntax tree.
    """

    def __init__(self, environment, source, filename=None):
        self.environment = environment
        if isinstance(source, str):
            source = source.decode(environment.template_charset, 'ignore')
        if isinstance(filename, unicode):
            filename = filename.encode('utf-8')
        self.source = source
        self.filename = filename
        self.closed = False
        self.blocks = set()
        self.no_variable_block = self.environment.lexer.no_variable_block
        self.stream = environment.lexer.tokenize(source, filename)

    def parse(self):
        pass
