Introduction
============

This is the documentation for the Jinja general purpose templating language.
Jinja is a library for Python that is designed to be flexible, fast and secure.

If you have any exposure to other text-based template languages, such as Smarty or
Django, you should feel right at home with Jinja.  It's both designer and
developer friendly by sticking to Python's principles and adding functionality
useful for templating environments.


Prerequisites
-------------

Jinja works with Python >= 3.5 and 2.7.

Jinja depends on `MarkupSafe`_. If you install via ``pip`` it will be
installed automatically.

.. _MarkupSafe: https://markupsafe.palletsprojects.com/


Installation
------------

You can install the most recent Jinja version using `pip`_::

    pip install Jinja

This will install Jinja in your Python installation's site-packages directory.

.. _pip: https://pypi.org/project/pip/


Basic API Usage
---------------

This section gives you a brief introduction to the Python API for Jinja
templates.

The most basic way to create a template and render it is through
:class:`~jinja.Template`.  This however is not the recommended way to
work with it if your templates are not loaded from strings but the file
system or another data source:

>>> from jinja import Template
>>> template = Template('Hello {{ name }}!')
>>> template.render(name='John Doe')
u'Hello John Doe!'

By creating an instance of :class:`~jinja.Template` you get back a new template
object that provides a method called :meth:`~jinja.Template.render` which when
called with a dict or keyword arguments expands the template.  The dict
or keywords arguments passed to the template are the so-called "context"
of the template.

What you can see here is that Jinja is using unicode internally and the
return value is an unicode string.  So make sure that your application is
indeed using unicode internally.
