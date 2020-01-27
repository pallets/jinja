.. _jinja-extensions:

Extensions
==========

Jinja supports extensions that can add extra filters, tests, globals or even
extend the parser.  The main motivation of extensions is to move often used
code into a reusable class like adding support for internationalization.


Adding Extensions
-----------------

Extensions are added to the Jinja environment at creation time.  Once the
environment is created additional extensions cannot be added.  To add an
extension pass a list of extension classes or import paths to the
``extensions`` parameter of the :class:`~jinja2.Environment` constructor.  The following
example creates a Jinja environment with the i18n extension loaded::

    jinja_env = Environment(extensions=['jinja2.ext.i18n'])


.. _i18n-extension:

i18n Extension
--------------

**Import name:** ``jinja2.ext.i18n``

The i18n extension can be used in combination with `gettext`_ or
`Babel`_.  When it's enabled, Jinja provides a ``trans`` statement that
marks a block as translatable and calls ``gettext``.

After enabling, an application has to provide ``gettext`` and
``ngettext`` functions, either globally or when rendering. A ``_()``
function is added as an alias to the ``gettext`` function.

Environment Methods
~~~~~~~~~~~~~~~~~~~

After enabling the extension, the environment provides the following
additional methods:

.. method:: jinja2.Environment.install_gettext_translations(translations, newstyle=False)

    Installs a translation globally for the environment. The
    ``translations`` object must implement ``gettext`` and ``ngettext``
    (or ``ugettext`` and ``ungettext`` for Python 2).
    :class:`gettext.NullTranslations`, :class:`gettext.GNUTranslations`,
    and `Babel`_\s ``Translations`` are supported.

    .. versionchanged:: 2.5 Added new-style gettext support.

.. method:: jinja2.Environment.install_null_translations(newstyle=False)

    Install no-op gettext functions. This is useful if you want to
    prepare the application for internationalization but don't want to
    implement the full system yet.

    .. versionchanged:: 2.5 Added new-style gettext support.

.. method:: jinja2.Environment.install_gettext_callables(gettext, ngettext, newstyle=False)

    Install the given ``gettext`` and ``ngettext`` callables into the
    environment. They should behave exactly like
    :func:`gettext.gettext` and :func:`gettext.ngettext` (or
    ``ugettext`` and ``ungettext`` for Python 2).

    If ``newstyle`` is activated, the callables are wrapped to work like
    newstyle callables.  See :ref:`newstyle-gettext` for more information.

    .. versionadded:: 2.5 Added new-style gettext support.

.. method:: jinja2.Environment.uninstall_gettext_translations()

    Uninstall the environment's globally installed translation.

.. method:: jinja2.Environment.extract_translations(source)

    Extract localizable strings from the given template node or source.

    For every string found this function yields a ``(lineno, function,
    message)`` tuple, where:

    -   ``lineno`` is the number of the line on which the string was
        found.
    -   ``function`` is the name of the ``gettext`` function used (if
        the string was extracted from embedded Python code).
    -   ``message`` is the string itself (``unicode`` on Python 2), or a
        tuple of strings for functions with multiple arguments.

    If `Babel`_ is installed, see :ref:`babel-integration` to extract
    the strings.

For a web application that is available in multiple languages but gives
all the users the same language (for example, multilingual forum
software installed for a French community), the translation may be
installed when the environment is created.

.. code-block:: python

    translations = get_gettext_translations()
    env = Environment(extensions=["jinja2.ext.i18n"])
    env.install_gettext_translations(translations)

The ``get_gettext_translations`` function would return the translator
for the current configuration, for example by using ``gettext.find``.

The usage of the ``i18n`` extension for template designers is covered in
:ref:`the template documentation <i18n-in-templates>`.

.. _gettext: https://docs.python.org/3/library/gettext.html
.. _Babel: http://babel.pocoo.org/


Whitespace Trimming
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2.10

Within ``{% trans %}`` blocks, it can be useful to trim line breaks and
whitespace so that the block of text looks like a simple string with
single spaces in the translation file.

Linebreaks and surrounding whitespace can be automatically trimmed by
enabling the ``ext.i18n.trimmed`` :ref:`policy <ext-i18n-trimmed>`.


.. _newstyle-gettext:

New Style Gettext
~~~~~~~~~~~~~~~~~

.. versionadded:: 2.5

New style gettext calls are less to type, less error prone, and support
autoescaping better.

You can use "new style" gettext calls by setting
``env.newstyle_gettext = True`` or passing ``newstyle=True`` to
``env.install_translations``. They are fully supported by the Babel
extraction tool, but might not work as expected with other extraction
tools.

With standard ``gettext`` calls, string formatting is a separate step
done with the ``|format`` filter. This requires duplicating work for
``ngettext`` calls.

.. sourcecode:: jinja

    {{ gettext("Hello, World!") }}
    {{ gettext("Hello, %(name)s!")|format(name=name) }}
    {{ ngettext(
           "%(num)d apple", "%(num)d apples", apples|count
       )|format(num=apples|count) }}

New style ``gettext`` make formatting part of the call, and behind the
scenes enforce more consistency.

.. sourcecode:: jinja

    {{ gettext("Hello, World!") }}
    {{ gettext("Hello, %(name)s!", name=name) }}
    {{ ngettext("%(num)d apple", "%(num)d apples", apples|count) }}

The advantages of newstyle gettext are:

-   There's no separate formatting step, you don't have to remember to
    use the ``|format`` filter.
-   Only named placeholders are allowed. This solves a common problem
    translators face because positional placeholders can't switch
    positions meaningfully. Named placeholders always carry semantic
    information about what value goes where.
-   String formatting is used even if no placeholders are used, which
    makes all strings use a consistent format. Remember to escape any
    raw percent signs as ``%%``, such as ``100%%``.
-   The translated string is marked safe, formatting performs escaping
    as needed. Mark a parameter as ``|safe`` if it has already been
    escaped.


Expression Statement
--------------------

**Import name:** ``jinja2.ext.do``

The "do" aka expression-statement extension adds a simple ``do`` tag to the
template engine that works like a variable expression but ignores the
return value.

.. _loopcontrols-extension:

Loop Controls
-------------

**Import name:** ``jinja2.ext.loopcontrols``

This extension adds support for ``break`` and ``continue`` in loops.  After
enabling, Jinja provides those two keywords which work exactly like in
Python.

.. _with-extension:

With Statement
--------------

**Import name:** ``jinja2.ext.with_``

.. versionchanged:: 2.9

    This extension is now built-in and no longer does anything.

.. _autoescape-extension:

Autoescape Extension
--------------------

**Import name:** ``jinja2.ext.autoescape``

.. versionchanged:: 2.9

    This extension was removed and is now built-in. Enabling the
    extension no longer does anything.


.. _debug-extension:

Debug Extension
---------------

**Import name:** ``jinja2.ext.debug``

Adds a ``{% debug %}`` tag to dump the current context as well as the
available filters and tests. This is useful to see what's available to
use in the template without setting up a debugger.


.. _writing-extensions:

Writing Extensions
------------------

.. module:: jinja2.ext

By writing extensions you can add custom tags to Jinja.  This is a non-trivial
task and usually not needed as the default tags and expressions cover all
common use cases.  The i18n extension is a good example of why extensions are
useful. Another one would be fragment caching.

When writing extensions you have to keep in mind that you are working with the
Jinja template compiler which does not validate the node tree you are passing
to it.  If the AST is malformed you will get all kinds of compiler or runtime
errors that are horrible to debug.  Always make sure you are using the nodes
you create correctly.  The API documentation below shows which nodes exist and
how to use them.


Example Extensions
------------------

Cache
~~~~~

The following example implements a ``cache`` tag for Jinja by using the
`cachelib`_ library:

.. literalinclude:: examples/cache_extension.py
    :language: python

And here is how you use it in an environment::

    from jinja2 import Environment
    from cachelib import SimpleCache

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

.. _cachelib: https://github.com/pallets/cachelib


Inline ``gettext``
~~~~~~~~~~~~~~~~~~

The following example demonstrates using :meth:`Extension.filter_stream`
to parse calls to the ``_()`` gettext function inline with static data
without needing Jinja blocks.

.. code-block:: html

        <h1>_(Welcome)</h1>
        <p>_(This is a paragraph)</p>

It requires the i18n extension to be loaded and configured.

.. literalinclude:: examples/inline_gettext_extension.py
    :language: python


Extension API
-------------

Extension
~~~~~~~~~

Extensions always have to extend the :class:`jinja2.ext.Extension` class:

.. autoclass:: Extension
    :members: preprocess, filter_stream, parse, attr, call_method

    .. attribute:: identifier

        The identifier of the extension.  This is always the true import name
        of the extension class and must not be changed.

    .. attribute:: tags

        If the extension implements custom tags this is a set of tag names
        the extension is listening for.


Parser
~~~~~~

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
        ``None``.

    .. attribute:: name

        The load name of the template.

    .. attribute:: stream

        The current :class:`~jinja2.lexer.TokenStream`

.. autoclass:: jinja2.lexer.TokenStream
   :members: push, look, eos, skip, __next__, next_if, skip_if, expect

   .. attribute:: current

        The current :class:`~jinja2.lexer.Token`.

.. autoclass:: jinja2.lexer.Token
    :members: test, test_any

    .. attribute:: lineno

        The line number of the token

    .. attribute:: type

        The type of the token.  This string is interned so you may compare
        it with arbitrary strings using the ``is`` operator.

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
change between Jinja versions but will stay backwards compatible.

For more information have a look at the repr of :meth:`jinja2.Environment.parse`.

.. module:: jinja2.nodes

.. jinja:nodes:: jinja2.nodes.Node

.. autoexception:: Impossible
