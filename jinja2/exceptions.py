# -*- coding: utf-8 -*-
"""
    jinja2.exceptions
    ~~~~~~~~~~~~~~~~~

    Jinja exceptions.

    :copyright: 2008 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class TemplateError(Exception):
    """Baseclass for all template errors."""


class UndefinedError(TemplateError):
    """Raised if a template tries to operate on :class:`Undefined`."""


class TemplateNotFound(IOError, LookupError, TemplateError):
    """Raised if a template does not exist."""

    def __init__(self, name):
        IOError.__init__(self, name)
        self.name = name


class TemplateSyntaxError(TemplateError):
    """Raised to tell the user that there is a problem with the template."""

    def __init__(self, message, lineno, name):
        TemplateError.__init__(self, '%s (line %s)' % (message, lineno))
        self.message = message
        self.lineno = lineno
        self.name = name


class TemplateAssertionError(TemplateSyntaxError):
    """Like a template syntax error, but covers cases where something in the
    template caused an error at compile time that wasn't necessarily caused
    by a syntax error.
    """


class TemplateRuntimeError(TemplateError):
    """A runtime error."""


class FilterArgumentError(Exception):
    """This error is raised if a filter was called with inappropriate
    arguments
    """
