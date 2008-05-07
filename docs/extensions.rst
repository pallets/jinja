.. _jinja-extensions:

Extensions
==========

.. module:: jinja2.ext

Jinja2 supports extensions that can add extra filters, tests, globals or even
extend the parser.  The main motivation of extensions is it to move often used
code into a reusable class like adding support for internationalization.


Adding Extensions
-----------------

Extensions are added to the Jinja2 environment at creation time.  Once the
environment is created additional extensions cannot be added.  To add an
extension pass a list of extension classes or import paths to the
`environment` parameter of the :class:`Environment` constructor.  The following
example creates a Jinja2 environment with the i18n extension loaded::

    jinja_env = Environment(extensions=['jinja.ext.i18n'])


Built-in Extensions
-------------------

.. _i18n-extension:

i18n
~~~~

The i18n extension can be used in combination with `gettext`_ or `babel`_.
If the i18n extension is enabled Jinja2 provides a `trans` statement that
marks the wrapped string as translatable and calls `gettext`.

After enabling dummy `_`, `gettext` and `ngettext` functions are added to
the template globals.  A internationalized application has to override those
methods with more useful versions.

For a web application that is available in multiple languages but gives all
the users the same language (for example a multilingual forum software
installed for a French community) may load the translations once and add the
translation methods to the environment at environment generation time::

    translations = get_gettext_translations()
    env = Environment(extensions=['jinja.ext.i18n'])
    env.globals.update(
        gettext=translations.ugettext,
        ngettext=translations.ungettext
    )

The `get_gettext_translations` function would return the translator for the
current configuration.  Keep in mind that Jinja2 uses unicode internally so
you must pass the `ugettext` and `ungettext` functions to the template.

The default `_` function injected by the extension calls `gettext`
automatically.

If you want to pass the gettext function into the context at render time
because you don't know the language/translations earlier and the optimizer
is enabled (which it is per default), you have to unregister the `gettext`
and `ugettext` functions first::

    del env.globals['gettext'], env.globals['ugettext']

Jinja2 also provides a way to extract recognized strings.  For one the
`jinja.ext` module provides a function that can return all the occurences
of gettext calls in a node (as returned by :meth:`Environment.parse`):

.. autofunction:: extract_from_ast

If `babel`_ is installed :ref:`the babel integration <babel-integration>`
can be used to.

The usage of the `i18n` extension for template designers is covered as part
:ref:`of the template documentation <i18n-in-templates>`.


.. _gettext: http://docs.python.org/dev/library/gettext
.. _babel: http://babel.edgewall.org/

.. _writing-extensions:

Writing Extensions
------------------

TODO
