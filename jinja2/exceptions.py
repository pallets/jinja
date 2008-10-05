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


class TemplateNotFound(IOError, LookupError, TemplateError):
    """Raised if a template does not exist."""

    def __init__(self, name):
        IOError.__init__(self, name)
        self.name = name


class TemplateSyntaxError(TemplateError):
    """Raised to tell the user that there is a problem with the template."""

    def __init__(self, message, lineno, name=None, filename=None):
        if not isinstance(message, unicode):
            message = message.decode('utf-8', 'replace')
        TemplateError.__init__(self, message.encode('utf-8'))
        self.lineno = lineno
        self.name = name
        self.filename = filename
        self.source = None
        self.message = message

    def __unicode__(self):
        location = 'line %d' % self.lineno
        name = self.filename or self.name
        if name:
            location = 'File "%s", %s' % (name, location)
        lines = [self.message, '  ' + location]

        # if the source is set, add the line to the output
        if self.source is not None:
            try:
                line = self.source.splitlines()[self.lineno - 1]
            except IndexError:
                line = None
            if line:
                lines.append('    ' + line.strip())

        return u'\n'.join(lines)

    def __str__(self):
        return unicode(self).encode('utf-8')


class TemplateAssertionError(TemplateSyntaxError):
    """Like a template syntax error, but covers cases where something in the
    template caused an error at compile time that wasn't necessarily caused
    by a syntax error.  However it's a direct subclass of
    :exc:`TemplateSyntaxError` and has the same attributes.
    """


class TemplateRuntimeError(TemplateError):
    """A generic runtime error in the template engine.  Under some situations
    Jinja may raise this exception.
    """


class UndefinedError(TemplateRuntimeError):
    """Raised if a template tries to operate on :class:`Undefined`."""


class SecurityError(TemplateRuntimeError):
    """Raised if a template tries to do something insecure if the
    sandbox is enabled.
    """


class FilterArgumentError(TemplateRuntimeError):
    """This error is raised if a filter was called with inappropriate
    arguments
    """
