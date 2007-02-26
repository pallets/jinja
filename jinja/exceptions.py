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


class TagNotFound(KeyError, TemplateError):
    """
    The parser looked for a specific tag in the tag library but was unable to find
    one.
    """

    def __init__(self, tagname):
        super(TagNotFound, self).__init__('The tag %r does not exist.' % tagname)
        self.tagname = tagname


class FilterNotFound(KeyError, TemplateError):
    """
    The template engine looked for a filter but was unable to find it.
    """

    def __init__(self, filtername):
        super(FilterNotFound, self).__init__('The filter %r does not exist.' % filtername)
        self.filtername = filtername


class TemplateSyntaxError(SyntaxError, TemplateError):
    """
    Raised to tell the user that there is a problem with the template.
    """

    def __init__(self, message, pos):
        super(TemplateSyntaxError, self).__init__(message)
        self.pos = pos


class TemplateRuntimeError(TemplateError):
    """
    Raised by the template engine if a tag encountered an error when
    rendering.
    """

    def __init__(self, message, pos):
        super(TemplateRuntimeError, self).__init__(message)
        self.pos = pos
