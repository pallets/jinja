API
===

.. module:: jinja2
    :synopsis: public Jinja2 API

This document describes the API to Jinja2 and not the template language.  It
will be most useful as reference to those implementing the template interface
to the application and not those who are creating Jinja2 templates.

Basics
------

Jinja2 uses a central object called the template :class:`Environment`.
Instances of this class are used to store the configuration, global objects
and are used to load templates from the file system or other locations.
Even if you are creating templates from string by using the constructor of
:class:`Template` class, an environment is created automatically for you.

Most applications will create one :class:`Environment` object on application
initialization and use that to load templates.  In some cases it's however
useful to have multiple environments side by side, if different configurations
are in use.

The simplest way to configure Jinja2 to load templates for your application
looks roughly like this::

    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('yourapplication', 'templates'))

This will create a template environment with the default settings and a
loader that looks up the templates in the `templates` folder inside the
`yourapplication` python package.  Different loaders are available
and you can also write your own if you want to load templates from a
database or other resources.

To load a template from this environment you just have to call the
:meth:`get_template` method which then returns the loaded :class:`Template`::

    template = env.get_template('mytemplate.html')

To render it with some variables, just call the :meth:`render` method::

    print template.render(the='variables', go='here')


Unicode
-------

Jinja2 is using unicode internally which means that you have to pass unicode
objects to the render function or bytestrings that only consist of ASCII
characters.  Additionally newlines are normalized to one end of line
sequence which is per default UNIX style (``\n``).


High Level API
--------------

.. autoclass:: Environment([options])
    :members: from_string, get_template, join_path, extend

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

        A dict of global variables.  These variables are always available
        in a template.  As long as no template was loaded it's safe
        to modify this dict.  For more details see :ref:`global-namespace`.
        For valid object names have a look at :ref:`identifier-naming`.

    .. automethod:: overlay([options])

    .. method:: undefined([hint,] [obj,] name[, exc])

        Creates a new :class:`Undefined` object for `name`.  This is useful
        for filters or functions that may return undefined objects for
        some operations.  All parameters except of `hint` should be provided
        as keyword parameters for better readability.  The `hint` is used as
        error message for the exception if provided, otherwise the error
        message generated from `obj` and `name` automatically.  The exception
        provided as `exc` is raised if something with the generated undefined
        object is done that the undefined object does not allow.  The default
        exception is :exc:`UndefinedError`.  If a `hint` is provided the
        `name` may be ommited.

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
        was accessed) it shold be passed to the undefined object, even if
        a custom `hint` is provided.  This gives undefined objects the
        possibility to enhance the error message.

.. autoclass:: Template
    :members: make_module, module, new_context

    .. attribute:: globals

        The dict with the globals of that template.  It's unsafe to modify
        this dict as it may be shared with other templates or the environment
        that loaded the template.

    .. attribute:: name

        The loading name of the template.  If the template was loaded from a
        string this is `None`.

    .. attribute:: filename

        The filename of the template on the file system if it was loaded from
        there.  Otherwise this is `None`.

    .. automethod:: render([context])

    .. automethod:: generate([context])

    .. automethod:: stream([context])


.. autoclass:: jinja2.environment.TemplateStream()
    :members: disable_buffering, enable_buffering


.. _identifier-naming:

Notes on Identifiers
--------------------

Jinja2 uses the regular Python 2.x naming rules.  Valid identifiers have to
match ``[a-zA-Z_][a-zA-Z0-9_]*``.  As a matter of fact non ASCII characters
are currently not allowed.  This limitation will probably go away as soon as
unicode identifiers are fully specified for Python 3.

Filters and tests are looked up in separate namespaces and have slightly
modified identifier syntax.  Filters and tests may contain dots to group
filters and tests by topic.  For example it's perfectly valid to add a
function into the filter dict and call it `to.unicode`.  The regular
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

The closest to regular Python behavior is the `StrictUndefined` which
disallows all operations beside testing if it's an undefined object.

.. autoclass:: jinja2.runtime.Undefined()

.. autoclass:: jinja2.runtime.DebugUndefined()

.. autoclass:: jinja2.runtime.StrictUndefined()

Undefined objects are created by calling :attr:`undefined`.


The Context
-----------

.. autoclass:: jinja2.runtime.Context()
    :members: resolve, get_exported, get_all

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


.. _loaders:

Loaders
-------

Loaders are responsible for loading templates from a resource such as the
file system.  The environment will keep the compiled modules in memory like
Python's `sys.modules`.  Unlike `sys.modules` however this cache is limited in
size by default and templates are automatically reloaded.
All loaders are subclasses of :class:`BaseLoader`.  If you want to create your
own loader, subclass :class:`BaseLoader` and override `get_source`.

.. autoclass:: jinja2.loaders.BaseLoader
    :members: get_source, load

Here a list of the builtin loaders Jinja2 provides:

.. autoclass:: jinja2.loaders.FileSystemLoader

.. autoclass:: jinja2.loaders.PackageLoader

.. autoclass:: jinja2.loaders.DictLoader

.. autoclass:: jinja2.loaders.FunctionLoader

.. autoclass:: jinja2.loaders.PrefixLoader

.. autoclass:: jinja2.loaders.ChoiceLoader


Utilities
---------

These helper functions and classes are useful if you add custom filters or
functions to a Jinja2 environment.

.. autofunction:: jinja2.filters.environmentfilter

.. autofunction:: jinja2.filters.contextfilter

.. autofunction:: jinja2.utils.environmentfunction

.. autofunction:: jinja2.utils.contextfunction

.. function:: escape(s)

    Convert the characters &, <, >, and " in string s to HTML-safe sequences.
    Use this if you need to display text that might contain such characters
    in HTML.  This function will not escaped objects that do have an HTML
    representation such as already escaped data.

.. autofunction:: jinja2.utils.clear_caches

.. autoclass:: jinja2.utils.Markup


Exceptions
----------

.. autoexception:: jinja2.exceptions.TemplateError

.. autoexception:: jinja2.exceptions.UndefinedError

.. autoexception:: jinja2.exceptions.TemplateNotFound

.. autoexception:: jinja2.exceptions.TemplateSyntaxError

    .. attribute:: message

        The error message as utf-8 bytestring.

    .. attribute:: lineno

        The line number where the error occurred

    .. attribute:: name

        The load name for the template as unicode string.

    .. attribute:: filename

        The filename that loaded the template as bytestring in the encoding
        of the file system (most likely utf-8 or mbcs on Windows systems).

    The reason why the filename and error message are bytestrings and not
    unicode strings is that Python 2.x is not using unicode for exceptions
    and tracebacks as well as the compiler.  This will change with Python 3.

.. autoexception:: jinja2.exceptions.TemplateAssertionError


.. _writing-filters:

Custom Filters
--------------

Custom filters are just regular Python functions that take the left side of
the filter as first argument and the the arguments passed to the filter as
extra arguments or keyword arguments.

For example in the filter ``{{ 42|myfilter(23) }}`` the function would be
called with ``myfilter(42, 23)``.  Here for example a simple filter that can
be applied to datetime objects to format them::

    def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
        return value.strftime(format)

You can register it on the template environment by updating the
:attr:`~Environment.filters` dict on the environment::

    environment.filters['datetimeformat'] = datetimeformat

Inside the template it can then be used as follows:

.. sourcecode:: jinja

    written on: {{ article.pub_date|datetimeformat }}
    publication date: {{ article.pub_date|datetimeformat('%d-%m-%Y') }}

Filters can also be passed the current template context or environment.  This
is useful if a filters wants to return an undefined value or check the current
:attr:`~Environment.autoescape` setting.  For this purpose two decorators
exist: :func:`environmentfilter` and :func:`contextfilter`.

Here a small example filter that breaks a text into HTML line breaks and
paragraphs and marks the return value as safe HTML string if autoescaping is
enabled::

    import re
    from jinja2 import environmentfilter, Markup, escape

    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

    @environmentfilter
    def nl2br(environment, value):
        result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                              for p in _paragraph_re.split(escape(value)))
        if environment.autoescape:
            result = Markup(result)
        return result

Context filters work the same just that the first argument is the current
active :class:`Context` rather then the environment.


.. _writing-tests:

Custom Tests
------------

Tests work like filters just that there is no way for a filter to get access
to the environment or context and that they can't be chained.  The return
value of a filter should be `True` or `False`.  The purpose of a filter is to
give the template designers the possibility to perform type and conformability
checks.

Here a simple filter that checks if a variable is a prime number::

    import math

    def is_prime(n):
        if n == 2:
            return True
        for i in xrange(2, int(math.ceil(math.sqrt(n))) + 1):
            if n % i == 0:
                return False
        return True
        

You can register it on the template environment by updating the
:attr:`~Environment.tests` dict on the environment::

    environment.tests['prime'] = is_prime

A template designer can then use the test like this:

.. sourcecode:: jinja

    {% if 42 is prime %}
        42 is a prime number
    {% else %}
        42 is not a prime number
    {% endif %}


.. _global-namespace:

The Global Namespace
--------------------

Variables stored in the :attr:`Environment.globals` dict are special as they
are available for imported templates too, even if they are imported without
context.  This is the place where you can put variables and functions
that should be available all the time.  Additionally :attr:`Template.globals`
exist that are variables available to a specific template that are available
to all :meth:`~Template.render` calls.


Low Level API
-------------

The low level API exposes functionality that can be useful to understand some
implementation details, debugging purposes or advanced :ref:`extension
<jinja-extensions>` techniques.

.. automethod:: Environment.lex

.. automethod:: Environment.parse

.. automethod:: Template.new_context

.. method:: Template.root_render_func(context)

    This is the low level render function.  It's passed a :class:`Context`
    that has to be created by :meth:`new_context` of the same template or
    a compatible template.  This render function is generated by the
    compiler from the template code and returns a generator that yields
    unicode strings.

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
