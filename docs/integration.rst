Integration
===========

Jinja provides some code for integration into other tools such as frameworks,
the `Babel`_ library or your favourite editor for fancy code highlighting.
This is a brief description of whats included.

Files to help integration are available
`here. <https://github.com/pallets/jinja/tree/master/ext>`_

.. _babel-integration:

Babel Integration
-----------------

Jinja provides support for extracting gettext messages from templates via a
`Babel`_ extractor entry point called `jinja2.ext.babel_extract`.  The Babel
support is implemented as part of the :ref:`i18n-extension` extension.

Gettext messages extracted from both `trans` tags and code expressions.

To extract gettext messages from templates, the project needs a Jinja section
in its Babel extraction method `mapping file`_:

.. sourcecode:: ini

    [jinja2: **/templates/**.html]
    encoding = utf-8

The syntax related options of the :class:`Environment` are also available as
configuration values in the mapping file.  For example to tell the extraction
that templates use ``%`` as `line_statement_prefix` you can use this code:

.. sourcecode:: ini

    [jinja2: **/templates/**.html]
    encoding = utf-8
    line_statement_prefix = %

:ref:`jinja-extensions` may also be defined by passing a comma separated list
of import paths as `extensions` value.  The i18n extension is added
automatically.

.. versionchanged:: 2.7

   Until 2.7 template syntax errors were always ignored.  This was done
   since many people are dropping non template html files into the
   templates folder and it would randomly fail.  The assumption was that
   testsuites will catch syntax errors in templates anyways.  If you don't
   want that behavior you can add ``silent=false`` to the settings and
   exceptions are propagated.

.. _mapping file: http://babel.pocoo.org/en/latest/messages.html#extraction-method-mapping-and-configuration

Pylons
------

With `Pylons`_ 0.9.7 onwards it's incredible easy to integrate Jinja into a
Pylons powered application.

The template engine is configured in `config/environment.py`.  The configuration
for Jinja looks something like that::

    from jinja2 import Environment, PackageLoader
    config['pylons.app_globals'].jinja_env = Environment(
        loader=PackageLoader('yourapplication', 'templates')
    )

After that you can render Jinja templates by using the `render_jinja` function
from the `pylons.templating` module.

Additionally it's a good idea to set the Pylons' `c` object into strict mode.
Per default any attribute to not existing attributes on the `c` object return
an empty string and not an undefined object.  To change this just use this
snippet and add it into your `config/environment.py`::

    config['pylons.strict_c'] = True

.. _Pylons: https://pylonshq.com/

TextMate
--------

There is a `bundle for TextMate`_ that supports syntax highlighting for Jinja 1
and Jinja 2 for text based templates as well as HTML. It also contains a few
often used snippets.

.. _bundle for TextMate: https://github.com/mitsuhiko/jinja2-tmbundle

Vim
---

A syntax plugin for `Vim`_ is available `from the jinja repository
<https://github.com/pallets/jinja/blob/master/ext/Vim/jinja.vim>`_. The script
supports Jinja 1 and Jinja 2. Once installed, two file types are available
(``jinja`` and ``htmljinja``). The first one is for text-based templates and the
second is for HTML templates. For HTML documents, the plugin attempts to
automatically detect Jinja syntax inside of existing HTML documents.

If you are using a plugin manager like `Pathogen`_, see the `vim-jinja
<https://github.com/mitsuhiko/vim-jinja>`_ repository for installing in the
``bundle/`` directory.

.. _Babel: http://babel.pocoo.org/
.. _Vim: https://www.vim.org/
.. _Pathogen: https://github.com/tpope/vim-pathogen
