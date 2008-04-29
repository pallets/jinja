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


High Level API
--------------

.. autoclass:: jinja2.environment.Environment
    :members: from_string, get_template, join_path

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
        loaded it's safe to add new filters or remove old.

    .. attribute:: tests

        A dict of test funcitons for this environment.  As long as no
        template way loaded it's safe to modify this dict.

    .. attribute:: globals

        A dict of global variables.  These variables are always available
        in a template and (if the optimizer is enabled) may not be
        override by templates.  As long as no template was loaded it's safe
        to modify this dict.


.. autoclass:: jinja2.Template
    :members: render, stream, generate, module


.. autoclass:: jinja2.environment.TemplateStream
    :members: disable_buffering, enable_buffering


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

.. autoclass:: jinja2.runtime.Undefined

.. autoclass:: jinja2.runtime.DebugUndefined

.. autoclass:: jinja2.runtime.StrictUndefined


Loaders
-------

Loaders are responsible for loading templates from a resource such as the
file system and for keeping the compiled modules in memory.  These work like
Python's `sys.modules` which keeps the imported templates in memory.  Unlike
`sys.modules` however this cache is limited in size by default and templates
are automatically reloaded.  Each loader that extends :class:`BaseLoader`
supports this caching and accepts two parameters to configure it:

`cache_size`
    The size of the cache.  Per default this is ``50`` which means that if
    more than 50 templates are loaded the loader will clean out the least
    recently used template.  If the cache size is set to ``0`` templates are
    recompiled all the time, if the cache size is ``-1`` the cache will not
    be cleaned.

`auto_reload`
    Some loaders load templates from locations where the template sources
    may change (ie: file system or database).  If `auto_reload` is set to
    `True` (default) every time a template is requested the loader checks
    if the source changed and if yes, it will reload the template.  For
    higher performance it's possible to disable that.

.. autoclass:: jinja2.loaders.FileSystemLoader

.. autoclass:: jinja2.loaders.PackageLoader

.. autoclass:: jinja2.loaders.DictLoader

.. autoclass:: jinja2.loaders.FunctionLoader

.. autoclass:: jinja2.loaders.PrefixLoader

.. autoclass:: jinja2.loaders.ChoiceLoader

All loaders are subclasses of :class:`BaseLoader`.  If you want to create your
own loader, subclass :class:`BaseLoader` and override `get_source`.

.. autoclass:: jinja2.loaders.BaseLoader
    :members: get_source, load


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

.. autoclass:: jinja2.utils.Markup


Exceptions
----------

.. autoclass:: jinja2.exceptions.TemplateError

.. autoclass:: jinja2.exceptions.UndefinedError

.. autoclass:: jinja2.exceptions.TemplateNotFound

.. autoclass:: jinja2.exceptions.TemplateSyntaxError

.. autoclass:: jinja2.exceptions.TemplateAssertionError
