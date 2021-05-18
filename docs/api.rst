API
===

.. module:: jinja2
    :noindex:
    :synopsis: public Jinja API

This document describes the API to Jinja and not the template language
(for that, see :doc:`/templates`). It will be most useful as reference
to those implementing the template interface to the application and not
those who are creating Jinja templates.

Basics
------

Jinja uses a central object called the template :class:`Environment`.
Instances of this class are used to store the configuration and global objects,
and are used to load templates from the file system or other locations.
Even if you are creating templates from strings by using the constructor of
:class:`Template` class, an environment is created automatically for you,
albeit a shared one.

Most applications will create one :class:`Environment` object on application
initialization and use that to load templates.  In some cases however, it's
useful to have multiple environments side by side, if different configurations
are in use.

The simplest way to configure Jinja to load templates for your
application is to use :class:`~loaders.PackageLoader`.

.. code-block:: python

    from jinja2 import Environment, PackageLoader, select_autoescape
    env = Environment(
        loader=PackageLoader("yourapp"),
        autoescape=select_autoescape()
    )

This will create a template environment with a loader that looks up
templates in the ``templates`` folder inside the ``yourapp`` Python
package (or next to the ``yourapp.py`` Python module). It also enables
autoescaping for HTML files. This loader only requires that ``yourapp``
is importable, it figures out the absolute path to the folder for you.

Different loaders are available to load templates in other ways or from
other locations. They're listed in the `Loaders`_ section below. You can
also write your own if you want to load templates from a source that's
more specialized to your project.

To load a template from this environment, call the :meth:`get_template`
method, which returns the loaded :class:`Template`.

.. code-block:: python

    template = env.get_template("mytemplate.html")

To render it with some variables, call the :meth:`render` method.

.. code-block:: python

    print(template.render(the="variables", go="here"))

Using a template loader rather than passing strings to :class:`Template`
or :meth:`Environment.from_string` has multiple advantages.  Besides being
a lot easier to use it also enables template inheritance.

.. admonition:: Notes on Autoescaping

   In future versions of Jinja we might enable autoescaping by default
   for security reasons.  As such you are encouraged to explicitly
   configure autoescaping now instead of relying on the default.


High Level API
--------------

The high-level API is the API you will use in the application to load and
render Jinja templates.  The :ref:`low-level-api` on the other side is only
useful if you want to dig deeper into Jinja or :ref:`develop extensions
<jinja-extensions>`.

.. autoclass:: Environment([options])
    :members: from_string, get_template, select_template,
              get_or_select_template, join_path, extend, compile_expression,
              compile_templates, list_templates, add_extension

    .. attribute:: shared

        If a template was created by using the :class:`Template` constructor
        an environment is created automatically.  These environments are
        created as shared environments which means that multiple templates
        may have the same anonymous environment.  For all shared environments
        this attribute is `True`, else `False`.

    .. attribute:: sandboxed

        If the environment is sandboxed this attribute is `True`.  For the
        sandbox mode have a look at the documentation for the
        :class:`~jinja2.sandbox.SandboxedEnvironment`.

    .. attribute:: filters

        A dict of filters for this environment.  As long as no template was
        loaded it's safe to add new filters or remove old.  For custom filters
        see :ref:`writing-filters`.  For valid filter names have a look at
        :ref:`identifier-naming`.

    .. attribute:: tests

        A dict of test functions for this environment.  As long as no
        template was loaded it's safe to modify this dict.  For custom tests
        see :ref:`writing-tests`.  For valid test names have a look at
        :ref:`identifier-naming`.

    .. attribute:: globals

        A dict of variables that are available in every template loaded
        by the environment. As long as no template was loaded it's safe
        to modify this. For more details see :ref:`global-namespace`.
        For valid object names see :ref:`identifier-naming`.

    .. attribute:: policies

        A dictionary with :ref:`policies`.  These can be reconfigured to
        change the runtime behavior or certain template features.  Usually
        these are security related.

    .. attribute:: code_generator_class

       The class used for code generation.  This should not be changed
       in most cases, unless you need to modify the Python code a
       template compiles to.

    .. attribute:: context_class

       The context used for templates.  This should not be changed
       in most cases, unless you need to modify internals of how
       template variables are handled.  For details, see
       :class:`~jinja2.runtime.Context`.

    .. automethod:: overlay([options])

    .. method:: undefined([hint, obj, name, exc])

        Creates a new :class:`Undefined` object for `name`.  This is useful
        for filters or functions that may return undefined objects for
        some operations.  All parameters except of `hint` should be provided
        as keyword parameters for better readability.  The `hint` is used as
        error message for the exception if provided, otherwise the error
        message will be generated from `obj` and `name` automatically.  The exception
        provided as `exc` is raised if something with the generated undefined
        object is done that the undefined object does not allow.  The default
        exception is :exc:`UndefinedError`.  If a `hint` is provided the
        `name` may be omitted.

        The most common way to create an undefined object is by providing
        a name only::

            return environment.undefined(name='some_name')

        This means that the name `some_name` is not defined.  If the name
        was from an attribute of an object it makes sense to tell the
        undefined object the holder object to improve the error message::

            if not hasattr(obj, 'attr'):
                return environment.undefined(obj=obj, name='attr')

        For a more complex example you can provide a hint.  For example
        the :func:`first` filter creates an undefined object that way::

            return environment.undefined('no first item, sequence was empty')

        If it the `name` or `obj` is known (for example because an attribute
        was accessed) it should be passed to the undefined object, even if
        a custom `hint` is provided.  This gives undefined objects the
        possibility to enhance the error message.

.. autoclass:: Template
    :members: module, make_module

    .. attribute:: globals

        A dict of variables that are available every time the template
        is rendered, without needing to pass them during render. This
        should not be modified, as depending on how the template was
        loaded it may be shared with the environment and other
        templates.

        Defaults to :attr:`Environment.globals` unless extra values are
        passed to :meth:`Environment.get_template`.

        Globals are only intended for data that is common to every
        render of the template. Specific data should be passed to
        :meth:`render`.

        See :ref:`global-namespace`.

    .. attribute:: name

        The loading name of the template.  If the template was loaded from a
        string this is `None`.

    .. attribute:: filename

        The filename of the template on the file system if it was loaded from
        there.  Otherwise this is `None`.

    .. automethod:: render([context])

    .. automethod:: generate([context])

    .. automethod:: stream([context])

    .. automethod:: render_async([context])

    .. automethod:: generate_async([context])


.. autoclass:: jinja2.environment.TemplateStream()
    :members: disable_buffering, enable_buffering, dump


Autoescaping
------------

.. versionchanged:: 2.4

Jinja now comes with autoescaping support.  As of Jinja 2.9 the
autoescape extension is removed and built-in.  However autoescaping is
not yet enabled by default though this will most likely change in the
future.  It's recommended to configure a sensible default for
autoescaping.  This makes it possible to enable and disable autoescaping
on a per-template basis (HTML versus text for instance).

.. autofunction:: jinja2.select_autoescape

Here a recommended setup that enables autoescaping for templates ending
in ``'.html'``, ``'.htm'`` and ``'.xml'`` and disabling it by default
for all other extensions.  You can use the :func:`~jinja2.select_autoescape`
function for this::

    from jinja2 import Environment, PackageLoader, select_autoescape
    env = Environment(autoescape=select_autoescape(['html', 'htm', 'xml']),
                      loader=PackageLoader('mypackage'))

The :func:`~jinja.select_autoescape` function returns a function that
works roughly like this::

    def autoescape(template_name):
        if template_name is None:
            return False
        if template_name.endswith(('.html', '.htm', '.xml'))

When implementing a guessing autoescape function, make sure you also
accept `None` as valid template name.  This will be passed when generating
templates from strings.  You should always configure autoescaping as
defaults in the future might change.

Inside the templates the behaviour can be temporarily changed by using
the `autoescape` block (see :ref:`autoescape-overrides`).


.. _identifier-naming:

Notes on Identifiers
--------------------

Jinja uses Python naming rules. Valid identifiers can be any combination
of characters accepted by Python.

Filters and tests are looked up in separate namespaces and have slightly
modified identifier syntax.  Filters and tests may contain dots to group
filters and tests by topic.  For example it's perfectly valid to add a
function into the filter dict and call it `to.str`.  The regular
expression for filter and test identifiers is
``[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*```.


Undefined Types
---------------

These classes can be used as undefined types.  The :class:`Environment`
constructor takes an `undefined` parameter that can be one of those classes
or a custom subclass of :class:`Undefined`.  Whenever the template engine is
unable to look up a name or access an attribute one of those objects is
created and returned.  Some operations on undefined values are then allowed,
others fail.

The closest to regular Python behavior is the :class:`StrictUndefined` which
disallows all operations beside testing if it's an undefined object.

.. autoclass:: jinja2.Undefined()

    .. attribute:: _undefined_hint

        Either `None` or a string with the error message for the
        undefined object.

    .. attribute:: _undefined_obj

        Either `None` or the owner object that caused the undefined object
        to be created (for example because an attribute does not exist).

    .. attribute:: _undefined_name

        The name for the undefined variable / attribute or just `None`
        if no such information exists.

    .. attribute:: _undefined_exception

        The exception that the undefined object wants to raise.  This
        is usually one of :exc:`UndefinedError` or :exc:`SecurityError`.

    .. method:: _fail_with_undefined_error(\*args, \**kwargs)

        When called with any arguments this method raises
        :attr:`_undefined_exception` with an error message generated
        from the undefined hints stored on the undefined object.

.. autoclass:: jinja2.ChainableUndefined()

.. autoclass:: jinja2.DebugUndefined()

.. autoclass:: jinja2.StrictUndefined()

There is also a factory function that can decorate undefined objects to
implement logging on failures:

.. autofunction:: jinja2.make_logging_undefined

Undefined objects are created by calling :attr:`undefined`.

.. admonition:: Implementation

    :class:`Undefined` is implemented by overriding the special
    ``__underscore__`` methods. For example the default
    :class:`Undefined` class implements ``__str__`` to returns an empty
    string, while ``__int__`` and others fail with an exception. To
    allow conversion to int by returning ``0`` you can implement your
    own subclass.

    .. code-block:: python

        class NullUndefined(Undefined):
            def __int__(self):
                return 0

            def __float__(self):
                return 0.0

    To disallow a method, override it and raise
    :attr:`~Undefined._undefined_exception`.  Because this is very
    common there is the helper method
    :meth:`~Undefined._fail_with_undefined_error` that raises the error
    with the correct information. Here's a class that works like the
    regular :class:`Undefined` but fails on iteration::

        class NonIterableUndefined(Undefined):
            def __iter__(self):
                self._fail_with_undefined_error()


The Context
-----------

.. autoclass:: jinja2.runtime.Context()
    :members: get, resolve, resolve_or_missing, get_exported, get_all

    .. attribute:: parent

        A dict of read only, global variables the template looks up.  These
        can either come from another :class:`Context`, from the
        :attr:`Environment.globals` or :attr:`Template.globals` or points
        to a dict created by combining the globals with the variables
        passed to the render function.  It must not be altered.

    .. attribute:: vars

        The template local variables.  This list contains environment and
        context functions from the :attr:`parent` scope as well as local
        modifications and exported variables from the template.  The template
        will modify this dict during template evaluation but filters and
        context functions are not allowed to modify it.

    .. attribute:: environment

        The environment that loaded the template.

    .. attribute:: exported_vars

        This set contains all the names the template exports.  The values for
        the names are in the :attr:`vars` dict.  In order to get a copy of the
        exported variables as dict, :meth:`get_exported` can be used.

    .. attribute:: name

        The load name of the template owning this context.

    .. attribute:: blocks

        A dict with the current mapping of blocks in the template.  The keys
        in this dict are the names of the blocks, and the values a list of
        blocks registered.  The last item in each list is the current active
        block (latest in the inheritance chain).

    .. attribute:: eval_ctx

        The current :ref:`eval-context`.

    .. automethod:: jinja2.runtime.Context.call(callable, \*args, \**kwargs)


.. admonition:: Implementation

    Context is immutable for the same reason Python's frame locals are
    immutable inside functions.  Both Jinja and Python are not using the
    context / frame locals as data storage for variables but only as primary
    data source.

    When a template accesses a variable the template does not define, Jinja
    looks up the variable in the context, after that the variable is treated
    as if it was defined in the template.


.. _loaders:

Loaders
-------

Loaders are responsible for loading templates from a resource such as the
file system.  The environment will keep the compiled modules in memory like
Python's `sys.modules`.  Unlike `sys.modules` however this cache is limited in
size by default and templates are automatically reloaded.
All loaders are subclasses of :class:`BaseLoader`.  If you want to create your
own loader, subclass :class:`BaseLoader` and override `get_source`.

.. autoclass:: jinja2.BaseLoader
    :members: get_source, load

Here a list of the builtin loaders Jinja provides:

.. autoclass:: jinja2.FileSystemLoader

.. autoclass:: jinja2.PackageLoader

.. autoclass:: jinja2.DictLoader

.. autoclass:: jinja2.FunctionLoader

.. autoclass:: jinja2.PrefixLoader

.. autoclass:: jinja2.ChoiceLoader

.. autoclass:: jinja2.ModuleLoader


.. _bytecode-cache:

Bytecode Cache
--------------

Jinja 2.1 and higher support external bytecode caching.  Bytecode caches make
it possible to store the generated bytecode on the file system or a different
location to avoid parsing the templates on first use.

This is especially useful if you have a web application that is initialized on
the first request and Jinja compiles many templates at once which slows down
the application.

To use a bytecode cache, instantiate it and pass it to the :class:`Environment`.

.. autoclass:: jinja2.BytecodeCache
    :members: load_bytecode, dump_bytecode, clear

.. autoclass:: jinja2.bccache.Bucket
    :members: write_bytecode, load_bytecode, bytecode_from_string,
              bytecode_to_string, reset

    .. attribute:: environment

        The :class:`Environment` that created the bucket.

    .. attribute:: key

        The unique cache key for this bucket

    .. attribute:: code

        The bytecode if it's loaded, otherwise `None`.


Builtin bytecode caches:

.. autoclass:: jinja2.FileSystemBytecodeCache

.. autoclass:: jinja2.MemcachedBytecodeCache


Async Support
-------------

.. versionadded:: 2.9

Jinja supports the Python ``async`` and ``await`` syntax. For the
template designer, this support (when enabled) is entirely transparent,
templates continue to look exactly the same. However, developers should
be aware of the implementation as it affects what types of APIs you can
use.

By default, async support is disabled. Enabling it will cause the
environment to compile different code behind the scenes in order to
handle async and sync code in an asyncio event loop. This has the
following implications:

-   Template rendering requires an event loop to be available to the
    current thread. :func:`asyncio.get_running_loop` must return an
    event loop.
-   The compiled code uses ``await`` for functions and attributes, and
    uses ``async for`` loops. In order to support using both async and
    sync functions in this context, a small wrapper is placed around
    all calls and access, which adds overhead compared to purely async
    code.
-   Sync methods and filters become wrappers around their corresponding
    async implementations where needed. For example, ``render`` invokes
    ``async_render``, and ``|map`` supports async iterables.

Awaitable objects can be returned from functions in templates and any
function call in a template will automatically await the result. The
``await`` you would normally add in Python is implied. For example, you
can provide a method that asynchronously loads data from a database, and
from the template designer's point of view it can be called like any
other function.


.. _policies:

Policies
--------

Starting with Jinja 2.9 policies can be configured on the environment
which can slightly influence how filters and other template constructs
behave.  They can be configured with the
:attr:`~jinja2.Environment.policies` attribute.

Example::

    env.policies['urlize.rel'] = 'nofollow noopener'

``truncate.leeway``:
    Configures the leeway default for the `truncate` filter.  Leeway as
    introduced in 2.9 but to restore compatibility with older templates
    it can be configured to `0` to get the old behavior back.  The default
    is `5`.

``urlize.rel``:
    A string that defines the items for the `rel` attribute of generated
    links with the `urlize` filter.  These items are always added.  The
    default is `noopener`.

``urlize.target``:
    The default target that is issued for links from the `urlize` filter
    if no other target is defined by the call explicitly.

``urlize.extra_schemes``:
    Recognize URLs that start with these schemes in addition to the
    default ``http://``, ``https://``, and ``mailto:``.

``json.dumps_function``:
    If this is set to a value other than `None` then the `tojson` filter
    will dump with this function instead of the default one.  Note that
    this function should accept arbitrary extra arguments which might be
    passed in the future from the filter.  Currently the only argument
    that might be passed is `indent`.  The default dump function is
    ``json.dumps``.

``json.dumps_kwargs``:
    Keyword arguments to be passed to the dump function.  The default is
    ``{'sort_keys': True}``.

.. _ext-i18n-trimmed:

``ext.i18n.trimmed``:
    If this is set to `True`, ``{% trans %}`` blocks of the
    :ref:`i18n-extension` will always unify linebreaks and surrounding
    whitespace as if the `trimmed` modifier was used.


Utilities
---------

These helper functions and classes are useful if you add custom filters or
functions to a Jinja environment.

.. autofunction:: jinja2.pass_context

.. autofunction:: jinja2.pass_eval_context

.. autofunction:: jinja2.pass_environment

.. autofunction:: jinja2.contextfilter

.. autofunction:: jinja2.evalcontextfilter

.. autofunction:: jinja2.environmentfilter

.. autofunction:: jinja2.contextfunction

.. autofunction:: jinja2.evalcontextfunction

.. autofunction:: jinja2.environmentfunction

.. autofunction:: jinja2.clear_caches

.. autofunction:: jinja2.is_undefined


Exceptions
----------

.. autoexception:: jinja2.TemplateError

.. autoexception:: jinja2.UndefinedError

.. autoexception:: jinja2.TemplateNotFound

.. autoexception:: jinja2.TemplatesNotFound

.. autoexception:: jinja2.TemplateSyntaxError

    .. attribute:: message

        The error message.

    .. attribute:: lineno

        The line number where the error occurred.

    .. attribute:: name

        The load name for the template.

    .. attribute:: filename

        The filename that loaded the template in the encoding of the
        file system (most likely utf-8, or mbcs on Windows systems).

.. autoexception:: jinja2.TemplateRuntimeError

.. autoexception:: jinja2.TemplateAssertionError


.. _writing-filters:

Custom Filters
--------------

Filters are Python functions that take the value to the left of the
filter as the first argument and produce a new value. Arguments passed
to the filter are passed after the value.

For example, the filter ``{{ 42|myfilter(23) }}`` is called behind the
scenes as ``myfilter(42, 23)``.

Jinja comes with some :ref:`built-in filters <builtin-filters>`. To use
a custom filter, write a function that takes at least a ``value``
argument, then register it in :attr:`Environment.filters`.

Here's a filter that formats datetime objects:

.. code-block:: python

    def datetime_format(value, format="%H:%M %d-%m-%y"):
        return value.strftime(format)

    environment.filters["datetime_format"] = datetime_format

Now it can be used in templates:

.. sourcecode:: jinja

    {{ article.pub_date|datetimeformat }}
    {{ article.pub_date|datetimeformat("%B %Y") }}

Some decorators are available to tell Jinja to pass extra information to
the filter. The object is passed as the first argument, making the value
being filtered the second argument.

-   :func:`pass_environment` passes the :class:`Environment`.
-   :func:`pass_eval_context` passes the :ref:`eval-context`.
-   :func:`pass_context` passes the current
    :class:`~jinja2.runtime.Context`.

Here's a filter that converts line breaks into HTML ``<br>`` and ``<p>``
tags. It uses the eval context to check if autoescape is currently
enabled before escaping the input and marking the output safe.

.. code-block:: python

    import re
    from jinja2 import pass_eval_context
    from markupsafe import Markup, escape

    @pass_eval_context
    def nl2br(eval_ctx, value):
        br = "<br>\n"

        if eval_ctx.autoescape:
            value = escape(value)
            br = Markup(br)

        result = "\n\n".join(
            f"<p>{br.join(p.splitlines())}<\p>"
            for p in re.split(r"(?:\r\n|\r(?!\n)|\n){2,}", value)
        )
        return Markup(result) if autoescape else result


.. _writing-tests:

Custom Tests
------------

Test are Python functions that take the value to the left of the test as
the first argument, and return ``True`` or ``False``. Arguments passed
to the test are passed after the value.

For example, the test ``{{ 42 is even }}`` is called behind the scenes
as ``is_even(42)``.

Jinja comes with some :ref:`built-in tests <builtin-tests>`. To use a
custom tests, write a function that takes at least a ``value`` argument,
then register it in :attr:`Environment.tests`.

Here's a test that checks if a value is a prime number:

.. code-block:: python

    import math

    def is_prime(n):
        if n == 2:
            return True

        for i in range(2, int(math.ceil(math.sqrt(n))) + 1):
            if n % i == 0:
                return False

        return True

    environment.tests["prime"] = is_prime

Now it can be used in templates:

.. sourcecode:: jinja

    {% if value is prime %}
        {{ value }} is a prime number
    {% else %}
        {{ value }} is not a prime number
    {% endif %}

Some decorators are available to tell Jinja to pass extra information to
the filter. The object is passed as the first argument, making the value
being filtered the second argument.

-   :func:`pass_environment` passes the :class:`Environment`.
-   :func:`pass_eval_context` passes the :ref:`eval-context`.
-   :func:`pass_context` passes the current
    :class:`~jinja2.runtime.Context`.


.. _eval-context:

Evaluation Context
------------------

The evaluation context (short eval context or eval ctx) makes it
possible to activate and deactivate compiled features at runtime.

Currently it is only used to enable and disable automatic escaping, but
it can be used by extensions as well.

The ``autoescape`` setting should be checked on the evaluation context,
not the environment. The evaluation context will have the computed value
for the current template.

Instead of ``pass_environment``:

.. code-block:: python

    @pass_environment
    def filter(env, value):
        result = do_something(value)

        if env.autoescape:
            result = Markup(result)

        return result

Use ``pass_eval_context`` if you only need the setting:

.. code-block:: python

    @pass_eval_context
    def filter(eval_ctx, value):
        result = do_something(value)

        if eval_ctx.autoescape:
            result = Markup(result)

        return result

Or use ``pass_context`` if you need other context behavior as well:

.. code-block:: python

    @pass_context
    def filter(context, value):
        result = do_something(value)

        if context.eval_ctx.autoescape:
            result = Markup(result)

        return result

The evaluation context must not be modified at runtime.  Modifications
must only happen with a :class:`nodes.EvalContextModifier` and
:class:`nodes.ScopedEvalContextModifier` from an extension, not on the
eval context object itself.

.. autoclass:: jinja2.nodes.EvalContext

   .. attribute:: autoescape

      `True` or `False` depending on if autoescaping is active or not.

   .. attribute:: volatile

      `True` if the compiler cannot evaluate some expressions at compile
      time.  At runtime this should always be `False`.


.. _global-namespace:

The Global Namespace
--------------------

The global namespace stores variables and functions that should be
available without needing to pass them to :meth:`Template.render`. They
are also available to templates that are imported or included without
context. Most applications should only use :attr:`Environment.globals`.

:attr:`Environment.globals` are intended for data that is common to all
templates loaded by that environment. :attr:`Template.globals` are
intended for data that is common to all renders of that template, and
default to :attr:`Environment.globals` unless they're given in
:meth:`Environment.get_template`, etc. Data that is specific to a
render should be passed as context to :meth:`Template.render`.

Only one set of globals is used during any specific rendering. If
templates A and B both have template globals, and B extends A, then
only B's globals are used for both when using ``b.render()``.

Environment globals should not be changed after loading any templates,
and template globals should not be changed at any time after loading the
template. Changing globals after loading a template will result in
unexpected behavior as they may be shared between the environment and
other templates.


.. _low-level-api:

Low Level API
-------------

The low level API exposes functionality that can be useful to understand some
implementation details, debugging purposes or advanced :ref:`extension
<jinja-extensions>` techniques.  Unless you know exactly what you are doing we
don't recommend using any of those.

.. automethod:: Environment.lex

.. automethod:: Environment.parse

.. automethod:: Environment.preprocess

.. automethod:: Template.new_context

.. method:: Template.root_render_func(context)

    This is the low level render function.  It's passed a :class:`Context`
    that has to be created by :meth:`new_context` of the same template or
    a compatible template.  This render function is generated by the
    compiler from the template code and returns a generator that yields
    strings.

    If an exception in the template code happens the template engine will
    not rewrite the exception but pass through the original one.  As a
    matter of fact this function should only be called from within a
    :meth:`render` / :meth:`generate` / :meth:`stream` call.

.. attribute:: Template.blocks

    A dict of block render functions.  Each of these functions works exactly
    like the :meth:`root_render_func` with the same limitations.

.. attribute:: Template.is_up_to_date

    This attribute is `False` if there is a newer version of the template
    available, otherwise `True`.

.. admonition:: Note

    The low-level API is fragile.  Future Jinja versions will try not to
    change it in a backwards incompatible way but modifications in the Jinja
    core may shine through.  For example if Jinja introduces a new AST node
    in later versions that may be returned by :meth:`~Environment.parse`.

The Meta API
------------

.. versionadded:: 2.2

The meta API returns some information about abstract syntax trees that
could help applications to implement more advanced template concepts.  All
the functions of the meta API operate on an abstract syntax tree as
returned by the :meth:`Environment.parse` method.

.. autofunction:: jinja2.meta.find_undeclared_variables

.. autofunction:: jinja2.meta.find_referenced_templates
