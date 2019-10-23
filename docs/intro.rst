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

Jinja works with Python 2.7.x and >= 3.5.  If you are using Python
3.2 you can use an older release of Jinja (2.6) as support for Python 3.2
was dropped in Jinja version 2.7. The last release which supported Python 2.6
and 3.3 was Jinja 2.10.

If you wish to use the :class:`~jinja2.PackageLoader` class, you will also
need `setuptools`_ or `distribute`_ installed at runtime.

Installation
------------

You can install the most recent Jinja version using `pip`_::

    pip install Jinja2

This will install Jinja in your Python installation's site-packages directory.

Installing the development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  Install `git`_
2.  ``git clone git://github.com/pallets/jinja.git``
3.  ``cd jinja2``
4.  ``ln -s jinja2 /usr/lib/python2.X/site-packages``

As an alternative to steps 4 you can also do ``python setup.py develop``
which will install the package via `distribute` in development mode.  This also
has the advantage that the C extensions are compiled.

.. _distribute: https://pypi.org/project/distribute/
.. _setuptools: https://pypi.org/project/setuptools/
.. _pip: https://pypi.org/project/pip/
.. _git: https://git-scm.com/


MarkupSafe Dependency
~~~~~~~~~~~~~~~~~~~~~

As of version 2.7 Jinja depends on the `MarkupSafe`_ module. If you install
Jinja via ``pip`` it will be installed automatically for you.

.. _MarkupSafe: https://markupsafe.palletsprojects.com/

Basic API Usage
---------------

This section gives you a brief introduction to the Python API for Jinja
templates.

The most basic way to create a template and render it is through
:class:`~jinja2.Template`.  This however is not the recommended way to
work with it if your templates are not loaded from strings but the file
system or another data source:

>>> from jinja2 import Template
>>> template = Template('Hello {{ name }}!')
>>> template.render(name='John Doe')
u'Hello John Doe!'

By creating an instance of :class:`~jinja2.Template` you get back a new template
object that provides a method called :meth:`~jinja2.Template.render` which when
called with a dict or keyword arguments expands the template.  The dict
or keywords arguments passed to the template are the so-called "context"
of the template.

What you can see here is that Jinja is using unicode internally and the
return value is an unicode string.  So make sure that your application is
indeed using unicode internally.
