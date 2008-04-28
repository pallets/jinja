Introduction
============

This is the documentation for the Jinja2 general purpose templating language.
Jinja2 is a library for Python 2.4 and onwards that is designed to be flexible,
fast and secure.

If you have any exposure to other text-based template languages, such as Smarty or
Django, you should feel right at home with Jinja2.  It's both designer and
developer friendly by sticking to Python's principles and adding functionality
useful for templating environments.

The key-features are...

-   ... **configurable syntax**.  If you are generating LaTeX or other formats
    with Jinja you can change the delimiters to something that integrates better
    into the LaTeX markup.

-   ... **fast**.  While performance is not the primarily target of Jinja2 it's
    surprisingly fast.  The overhead compared to regular Python code was reduced
    to the very minimum.

-   ... **easy to debug**.  Jinja2 integrates directly into the python traceback
    system which allows you to debug Jinja templates with regular python
    debugging helpers.

-   ... **secure**.  It's possible to evaluate untrusted template code if the
    optional sandbox is enabled.  This allows Jinja2 to be used as templating
    language for applications where users may modify the template design.


Prerequisites
-------------

Jinja2 needs at least **Python 2.4** to run.  Additionally a working C-compiler
that can create python extensions should be installed for the debugger.  If no
C-compiler is available the `ctypes`_ module should be installed.

.. _ctypes: http://python.net/crew/theller/ctypes/


Basic API Usage
---------------

This section gives you a brief introduction to the Python API for Jinja templates.

The most basic way to create a template and render it is through
:class:`Template`.  This however is not the recommended way to work with it,
but the easiest

>>> from jinja2 import Template
>>> template = Template('Hello {{ name }}!')
>>> template.render(name='John Doe')
u'Hello John Doe!'

By creating an instance of :class:`Template` you get back a new template
object that provides a method called :meth:`~Template.render` which when
called with a dict or keyword arguments expands the template.  The dict
or keywords arguments passed to the template are the so-called "context"
of the template.
