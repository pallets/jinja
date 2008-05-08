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


.. _i18n-extension:

i18n Extension
--------------

Jinja2 currently comes with one extension, the i18n extension.  It can be
used in combination with `gettext`_ or `babel`_.  If the i18n extension is
enabled Jinja2 provides a `trans` statement that marks the wrapped string as
translatable and calls `gettext`.

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

By writing extensions you can add custom tags to Jinja2.  This is a non trival
task and usually not needed as the default tags and expressions cover all
common use cases.  The i18n extension is a good example of why extensions are
useful, another one would be fragment caching.

Example Extension
~~~~~~~~~~~~~~~~~

The following example implements a `cache` tag for Jinja2:

.. literalinclude:: cache_extension.py
    :language: python

In order to use the cache extension it makes sense to subclass the environment
to implement the `add_fragment_to_cache` and `load_fragment_from_cache`
methods.  The following example shows how to use the `Werkzeug`_ caching
with the extension from above::

    from jinja2 import Environment
    from werkzeug.contrib.cache import SimpleCache

    cache = SimpleCache()
    cache_prefix = 'tempalte_fragment/'

    class MyEnvironment(Environment):

        def __init__(self):
            Environment.__init__(self, extensions=[CacheExtension])

        def add_fragment_to_cache(self, key, value, timeout):
            cache.add(cache_prefix + key, value, timeout)

        def load_fragment_from_cache(self, key):
            return cache.get(cache_prefix + key)

.. _Werkzeug: http://werkzeug.pocoo.org/

Extension API
~~~~~~~~~~~~~

Extensions always have to extend the :class:`jinja2.ext.Extension` class:

.. autoclass:: Extension
    :members: parse, attr

    .. attribute:: identifier

        The identifier of the extension.  This is always the true import name
        of the extension class and must not be changed.

    .. attribute:: tags

        If the extension implements custom tags this is a set of tag names
        the extension is listening for.

Parser API
~~~~~~~~~~

The parser passed to :meth:`Extension.parse` provides ways to parse
expressions of different types.  The following methods may be used by
extensions:

.. autoclass:: jinja2.parser.Parser
    :members: parse_expression, parse_tuple, parse_statements, ignore_colon,
              free_identifier

    .. attribute:: filename

        The filename of the template the parser processes.  This is **not**
        the load name of the template which is unavailable at parsing time.
        For templates that were not loaded form the file system this is
        `None`.

    .. attribute:: stream

        The current :class:`~jinja2.lexer.TokenStream`

.. autoclass:: jinja2.lexer.TokenStream
   :members: push, look, eos, skip, next, expect

   .. attribute:: current

        The current :class:`~jinja2.lexer.Token`.

.. autoclass:: jinja2.lexer.Token
    :members: test, test_any

    .. attribute:: lineno

        The line number of the token

    .. attribute:: type

        The type of the token.  This string is interned so you may compare
        it with arbitrary strings using the `is` operator.

    .. attribute:: value

        The value of the token.

AST
~~~

The AST (Abstract Syntax Tree) is used to represent a template after parsing.
It's build of nodes that the compiler then converts into executable Python
code objects.  Extensions that provide custom statements can return nodes to
execute custom Python code.

The list below describes all nodes that are currently available.  The AST may
change between Jinja2 versions but will stay backwards compatible.

For more information have a look at the repr of :meth:`jinja2.Environment.parse`.

.. module:: jinja2.nodes

.. jinjanodes::

.. autoexception:: Impossible
