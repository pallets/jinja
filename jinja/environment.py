# -*- coding: utf-8 -*-
"""
    jinja.environment
    ~~~~~~~~~~~~~~~~~

    Provides a class that holds runtime and parsing time options.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja.lexer import Lexer
from jinja.parser import Parser
from jinja.exceptions import TagNotFound, FilterNotFound
from jinja.defaults import DEFAULT_TAGS, DEFAULT_FILTERS


class Environment(object):
    """
    The jinja environment.
    """

    def __init__(self,
                 block_start_string='{%',
                 block_end_string='%}',
                 variable_start_string='{{',
                 variable_end_string='}}',
                 comment_start_string='{#',
                 comment_end_string='#}',
                 template_charset='utf-8',
                 charset='utf-8',
                 loader=None,
                 tags=None,
                 filters=None):

        # lexer / parser information
        self.block_start_string = block_start_string
        self.block_end_string = block_end_string
        self.variable_start_string = variable_start_string
        self.variable_end_string = variable_end_string
        self.comment_start_string = comment_start_string
        self.comment_end_string = comment_end_string

        # other stuff
        self.template_charset = template_charset
        self.charset = charset
        self.loader = loader
        self.tags = tags or DEFAULT_TAGS.copy()
        self.filters = filters or DEFAULT_FILTERS.copy()

        # create lexer
        self.lexer = Lexer(self)

    def parse(self, source):
        """Function that creates a new parser and parses the source."""
        parser = Parser(self, source)
        return parser.parse_page()

    def get_tag(self, name):
        """
        Return the tag for a specific name. Raise a `TagNotFound` exception
        if a tag with this name is not registered.
        """
        if name not in self._tags:
            raise TagNotFound(name)
        return self._tags[name]

    def get_filter(self, name):
        """
        Return the filter for a given name. Raise a `FilterNotFound` exception
        if the requested filter is not registered.
        """
        if name not in self._filters:
            raise FilterNotFound(name)
        return self._filters[name]

    def to_unicode(self, value):
        """
        Convert a value to unicode with the rules defined on the environment.
        """
        if isinstance(value, unicode):
            return value
        else:
            try:
                return unicode(value)
            except UnicodeError:
                return str(value).decode(self.charset, 'ignore')
