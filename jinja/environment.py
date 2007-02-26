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
from jinja.datastructure import LoopContext, Undefined
from jinja.exceptions import FilterNotFound
from jinja.defaults import DEFAULT_FILTERS


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
        self.filters = filters or DEFAULT_FILTERS.copy()

        # create lexer
        self.lexer = Lexer(self)

    def parse(self, source):
        """Function that creates a new parser and parses the source."""
        parser = Parser(self, source)
        return parser.parse_page()

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

    def iterate(self, seq):
        """
        Helper function used by the python translator runtime code to
        iterate over a sequence.
        """
        try:
            length = len(seq)
        except TypeError:
            seq = list(seq)
            length = len(seq)
        loop_data = LoopContext(0, length)
        for item in seq:
            loop_data.index += 1
            yield loop_data, item

    def prepare_filter(self, name, *args):
        """
        Prepare a filter.
        """
        try:
            return self.filters[name](*args)
        except KeyError:
            raise FilterNotFound(name)

    def apply_filters(self, value, context, filters):
        """
        Apply a list of filters on the variable.
        """
        for f in filters:
            value = f(self, context, value)
        return value

    def get_attribute(self, obj, name):
        """
        Get the attribute name from obj.
        """
        try:
            return getattr(obj, name)
        except AttributeError:
            return obj[name]
        except:
            return Undefined
