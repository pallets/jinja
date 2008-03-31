# -*- coding: utf-8 -*-
"""
    jinja.exceptions
    ~~~~~~~~~~~~~~~~

    Jinja exceptions.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class TemplateError(RuntimeError):
    pass


class TemplateNotFound(IOError, LookupError, TemplateError):
    """
    Raised if a template does not exist.
    """

    def __init__(self, name):
        IOError.__init__(self, name)
        self.name = name


class TemplateSyntaxError(SyntaxError, TemplateError):
    """
    Raised to tell the user that there is a problem with the template.
    """

    def __init__(self, message, lineno, filename):
        SyntaxError.__init__(self, message)
        self.lineno = lineno
        self.filename = filename


class TemplateRuntimeError(TemplateError):
    """
    Raised by the template engine if a tag encountered an error when
    rendering.
    """
