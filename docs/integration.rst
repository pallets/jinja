Integration
===========

Jinja2 provides some code for integration into other tools such as frameworks,
the `Babel`_ library or your favourite editor for fancy code highlighting.
This is a brief description of whats included.

.. _babel-integration:

Babel Integration
-----------------

Jinja provides support for extracting gettext messages from templates via a
`Babel`_ extractor entry point called `jinja2.ext.babel_extract`.  The Babel
support is implemented as part of the :ref:`i18n-extension` extension.

Gettext messages extracted from both `trans` tags and code expressions.

To extract gettext messages from templates, the project needs a Jinja2 section
in its Babel extraction method `mapping file`_:

.. sourcecode:: ini

    [jinja: **/templates/**.html]
    encoding = utf-8

The syntax related options of the :class:`Environment` are also available as
configuration values in the mapping file.  For example to tell the extraction
that templates use ``%`` as `line_statement_prefix` you can use this code:

.. sourcecode:: ini

    [jinja: **/templates/**.html]
    encoding = utf-8
    line_statement_prefix = %

:ref:`jinja-extensions` may also be defined by passing a comma separated list
of import paths as `extensions` value.  The i18n extension is added
automatically.

.. _mapping file: http://babel.edgewall.org/wiki/Documentation/messages.html#extraction-method-mapping-and-configuration

Django
------

TODO

Pylons
------

TODO

WSGI
----

TODO

TextMate
--------

TODO

Vim
---

TODO

.. _Babel: http://babel.edgewall.org/
