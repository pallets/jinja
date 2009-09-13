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
    with Jinja2 you can change the delimiters to something that integrates better
    into the LaTeX markup.

-   ... **fast**.  While performance is not the primarily target of Jinja2 it's
    surprisingly fast.  The overhead compared to regular Python code was reduced
    to the very minimum.

-   ... **easy to debug**.  Jinja2 integrates directly into the python traceback
    system which allows you to debug Jinja2 templates with regular python
    debugging helpers.

-   ... **secure**.  It's possible to evaluate untrusted template code if the
    optional sandbox is enabled.  This allows Jinja2 to be used as templating
    language for applications where users may modify the template design.


Prerequisites
-------------

Jinja2 needs at least **Python 2.4** to run.  Additionally a working C-compiler
that can create python extensions should be installed for the debugger.  If no
C-compiler is available and you are using Python 2.4 the `ctypes`_ module
should be installed.

If you don't have a working C compiler and you are trying to install the source
release with the speedups you will get a compiler error.  This however can be
circumvented by passing the ``--without-speedups`` command line argument to the
setup script::

    $ python setup.py --with-speedups install

(As of Jinja 2.2, the speedups are disabled by default and can be enabled
with ``--with-speedups``.  See :ref:`enable-speedups`)

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

Note that the last command will automatically download and install
`setuptools`_ if you don't already have it installed. This requires a working
internet connection.

This will install Jinja2 into your Python installation's site-packages directory.

Installing the development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1.  Install `mercurial`_
2.  ``hg clone http://dev.pocoo.org/hg/jinja2-main jinja2``
3.  ``cd jinja2``
4.  ``ln -s jinja2 /usr/lib/python2.X/site-packages``

As an alternative to steps 4 you can also do ``python setup.py develop``
which will install the package via setuptools in development mode.  This also
has the advantage that the C extensions are compiled.

Alternative you can use `easy_install`_ to install the current development
snapshot::

    sudo easy_install Jinja2==dev

Or the new `pip`_ command::

    sudo pip install Jinja2==dev

.. _download page: http://pypi.python.org/pypi/Jinja2
.. _setuptools: http://peak.telecommunity.com/DevCenter/setuptools
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _pip: http://pypi.python.org/pypi/pip
.. _mercurial: http://www.selenic.com/mercurial/

.. _enable-speedups:

Enaable the speedups Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default Jinja2 will not compile the speedups module.  Enabling this
will fail if you don't have the Python headers or a working compiler.  This
is often the case if you are installing Jinja2 from a windows machine.

You can enable the speedups extension when installing using the
``--with-speedups`` flag::

    sudo python setup.py --with-speedups install



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
