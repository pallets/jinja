Introduction
============

This is the documentation for the Jinja2 general purpose templating language.
Jinja2 is a library for Python 2.4 and onwards that is designed to be flexible,
fast and secure.

If you have any exposure to other text-based template languages, such as Smarty or
Django, you should feel right at home with Jinja2.  It's both designer and
developer friendly by sticking to Python's principles and adding functionality
useful for templating environments.

Prerequisites
-------------

Jinja2 needs at least **Python 2.4** to run.  Additionally a working C-compiler
that can create python extensions should be installed for the debugger if you
are using Python 2.4.

If you don't have a working C-compiler and you are trying to install the source
release with the debugsupport you will get a compiler error.

.. _ctypes: http://python.net/crew/theller/ctypes/


Installation
------------

You have multiple ways to install Jinja2.  If you are unsure what to do, go
with the Python egg or tarball.

As a Python egg (via easy_install)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can install the most recent Jinja2 version using `easy_install`_ or `pip`_::

    easy_install Jinja2
    pip install Jinja2

This will install a Jinja2 egg in your Python installation's site-packages
directory.

(If you are installing from the windows command line omit the `sudo` and make
sure to run the command as user with administrator rights)

From the tarball release
~~~~~~~~~~~~~~~~~~~~~~~~~

1.  Download the most recent tarball from the `download page`_
2.  Unpack the tarball
3.  ``sudo python setup.py install``

Note that you either have to have setuptools or `distribute`_ installed,
the latter is preferred.

This will install Jinja2 into your Python installation's site-packages directory.

.. _distribute: http://pypi.python.org/pypi/distribute

Installing the development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  Install `git`_
2.  ``git clone git://github.com/mitsuhiko/jinja2.git``
3.  ``cd jinja2``
4.  ``ln -s jinja2 /usr/lib/python2.X/site-packages``

As an alternative to steps 4 you can also do ``python setup.py develop``
which will install the package via distribute in development mode.  This also
has the advantage that the C extensions are compiled.

.. _download page: http://pypi.python.org/pypi/Jinja2
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip: http://pypi.python.org/pypi/pip
.. _git: http://git-scm.org/


More Speed with MarkupSafe
~~~~~~~~~~~~~~~~~~~~~~~~~~

As of version 2.5.1 Jinja2 will check for an installed `MarkupSafe`_
module.  If it can find it, it will use the Markup class of that module
instead of the one that comes with Jinja2.  `MarkupSafe` replaces the
older speedups module that came with Jinja2 and has the advantage that is
has a better setup script and will automatically attempt to install the C
version and nicely fall back to a pure Python implementation if that is
not possible.

The C implementation of MarkupSafe is much faster and recommended when
using Jinja2 with autoescaping.

.. _MarkupSafe: http://pypi.python.org/pypi/MarkupSafe


Enable the debug support Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default Jinja2 will not compile the debug support module.  Enabling this
will fail if you don't have the Python headers or a working compiler.  This
is often the case if you are installing Jinja2 from a windows machine.

Because the debug support is only necessary for Python 2.4 you will not
have to do this unless you run 2.4::

    sudo python setup.py --with-debugsupport install


Basic API Usage
---------------

This section gives you a brief introduction to the Python API for Jinja2
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

What you can see here is that Jinja2 is using unicode internally and the
return value is an unicode string.  So make sure that your application is
indeed using unicode internally.


Experimental Python 3 Support
-----------------------------

Jinja 2.3 brings experimental support for Python 3.  It means that all
unittests pass on the new version, but there might still be small bugs in
there and behavior might be inconsistent.  If you notice any bugs, please
provide feedback in the `Jinja bug tracker`_.

Also please keep in mind that the documentation is written with Python 2
in mind, you will have to adapt the shown code examples to Python 3 syntax
for yourself.


.. _Jinja bug tracker: http://github.com/mitsuhiko/jinja2/issues
