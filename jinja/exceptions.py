# -*- coding: utf-8 -*-
"""
    jinja.exceptions
    ~~~~~~~~~~~~~~~~

    Jinja exceptions.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class TemplateError(RuntimeError):
    pass


class FilterNotFound(KeyError, TemplateError):
    """
    Raised if a filter does not exist.
    """

    def __init__(self, message):
        KeyError.__init__(self, message)


class TemplateSyntaxError(SyntaxError, TemplateError):
    """
    Raised to tell the user that there is a problem with the template.
    """

    def __init__(self, message, pos):
        SyntaxError.__init__(self, message)
        self.pos = pos


class TemplateRuntimeError(TemplateError):
    """
    Raised by the template engine if a tag encountered an error when
    rendering.
    """

    def __init__(self, message, pos):
        RuntimeError.__init__(self, message)
        self.pos = pos
