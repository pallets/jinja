.. _jinja-extensions:

Extensions
==========

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

    jinja_env = Environment(extensions=['jinja2.ext.i18n'])


.. _i18n-extension:

i18n Extension
--------------

**Import name:** `jinja2.ext.i18n`

Jinja2 currently comes with one extension, the i18n extension.  It can be
used in combination with `gettext`_ or `babel`_.  If the i18n extension is
enabled Jinja2 provides a `trans` statement that marks the wrapped string as
translatable and calls `gettext`.

After enabling dummy `_` function that forwards calls to `gettext` is added
to the environment globals.  An internationalized application then has to
provide at least an `gettext` and optoinally a `ngettext` function into the
namespace.  Either globally or for each rendering.

After enabling of the extension the environment provides the following
additional methods:

.. method:: jinja2.Environment.install_gettext_translations(translations)

    Installs a translation globally for that environment.  The tranlations
    object provided must implement at least `ugettext` and `ungettext`.
    The `gettext.NullTranslations` and `gettext.GNUTranslations` classes
    as well as `Babel`_\s `Translations` class are supported.

.. method:: jinja2.Environment.install_null_translations()

    Install dummy gettext functions.  This is useful if you want to prepare
    the application for internationalization but don't want to implement the
    full internationalization system yet.

.. method:: jinja2.Environment.uninstall_gettext_translations()

    Uninstall the translations again.

.. method:: jinja2.Environment.extract_translations(source)

    Extract localizable strings from the given template node or source.

    For every string found this function yields a ``(lineno, function,
    message)`` tuple, where:

    * `lineno` is the number of the line on which the string was found,
    * `function` is the name of the `gettext` function used (if the
      string was extracted from embedded Python code), and
    *  `message` is the string itself (a `unicode` object, or a tuple
       of `unicode` objects for functions with multiple string arguments).

    If `Babel`_ is installed :ref:`the babel integration <babel-integration>`
    can be used to extract strings for babel.

For a web application that is available in multiple languages but gives all
the users the same language (for example a multilingual forum software
installed for a French community) may load the translations once and add the
translation methods to the environment at environment generation time::

    translations = get_gettext_translations()
    env = Environment(extensions=['jinja2.ext.i18n'])
    env.install_gettext_translations(translations)

The `get_gettext_translations` function would return the translator for the
current configuration.  (For example by using `gettext.find`)

The usage of the `i18n` extension for template designers is covered as part
:ref:`of the template documentation <i18n-in-templates>`.

.. _gettext: http://docs.python.org/dev/library/gettext
.. _Babel: http://babel.edgewall.org/


Expression Statement
--------------------

**Import name:** `jinja2.ext.do`

The "do" aka expression-statement extension adds a simple `do` tag to the
template engine that works like a variable expression but ignores the
return value.

.. _loopcontrols-extension:

Loop Controls
-------------

**Import name:** `jinja2.ext.loopcontrols`

This extension adds support for `break` and `continue` in loops.  After
enabling Jinja2 provides those two keywords which work exactly like in
Python.

.. _with-extension:

With Statement
--------------

**Import name:** `jinja2.ext.with_`

.. versionadded:: 2.3

This extension adds support for the with keyword.  Using this keyword it
is possible to enforce a nested scope in a template.  Variables can be
declared directly in the opening block of the with statement or using a
standard `set` statement directly within.


.. _writing-extensions:

Writing Extensions
------------------

.. module:: jinja2.ext

By writing extensions you can add custom tags to Jinja2.  This is a non trival
task and usually not needed as the default tags and expressions cover all
common use cases.  The i18n extension is a good example of why extensions are
useful, another one would be fragment caching.

When writing extensions you have to keep in mind that you are working with the
Jinja2 template compiler which does not validate the node tree you are possing
to it.  If the AST is malformed you will get all kinds of compiler or runtime
errors that are horrible to debug.  Always make sure you are using the nodes
you create correctly.  The API documentation below shows which nodes exist and
how to use them.

Example Extension
~~~~~~~~~~~~~~~~~

The following example implements a `cache` tag for Jinja2 by using the
`Werkzeug`_ caching contrib module:

.. literalinclude:: cache_extension.py
    :language: python

And here is how you use it in an environment::

    from jinja2 import Environment
    from werkzeug.contrib.cache import SimpleCache

    env = Environment(extensions=[FragmentCacheExtension])
    env.fragment_cache = SimpleCache()

Inside the template it's then possible to mark blocks as cacheable.  The
following example caches a sidebar for 300 seconds:

.. sourcecode:: html+jinja

    {% cache 'sidebar', 300 %}
    <div class="sidebar">
        ...
    </div>
    {% endcache %}

.. _Werkzeug: http://werkzeug.pocoo.org/

Extension API
~~~~~~~~~~~~~

Extensions always have to extend the :class:`jinja2.ext.Extension` class:

.. autoclass:: Extension
    :members: preprocess, filter_stream, parse, attr, call_method

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
    :members: parse_expression, parse_tuple, parse_assign_target,
              parse_statements, free_identifier, fail

    .. attribute:: filename

        The filename of the template the parser processes.  This is **not**
        the load name of the template.  For the load name see :attr:`name`.
        For templates that were not loaded form the file system this is
        `None`.

    .. attribute:: name

        The load name of the template.

    .. attribute:: stream

        The current :class:`~jinja2.lexer.TokenStream`

.. autoclass:: jinja2.lexer.TokenStream
   :members: push, look, eos, skip, next, next_if, skip_if, expect

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

There is also a utility function in the lexer module that can count newline
characters in strings:

.. autofunction:: jinja2.lexer.count_newlines

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
