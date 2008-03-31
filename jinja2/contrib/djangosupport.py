# -*- coding: utf-8 -*-
"""
    jinja.contrib.djangosupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Support for the django framework. This module is quite magical because it
    just exports one single function, the `configure` function which is used
    to create a new Jinja environment and setup a special module called
    `django.contrib.jinja` which exports a couple of functions useful for Jinja.

    Quickstart
    ==========

    To get started execute the following code at the bottom of your settings.py
    or in some general application file such as urls.py or a central module. The
    only thing that matters is that it's executed right *after* the settings
    were set up and *before* `django.contrib.jinja` is imported::

        from jinja.contrib import djangosupport
        djangosupport.configure()

    What this does is setting up a Jinja environment for this django instance
    with loaders for `TEMPLATE_DIRS` etc.  It also converts a couple of default
    django filters such as `date` and `timesince` which are not available in
    Jinja per default.  If you want to change the list you can provide others
    by passing a list with filter import names as `convert_filters` keyword
    argument.

    All other keyword arguments are forwarded to the environment.  If you want
    to provide a loader yourself pass it a loader keyword argument.

    Rendering Templates
    ===================

    To render a template you can use the functions `render_to_string` or
    `render_to_response` from the `django.contrib.jinja` module::

        from django.contrib.jinja import render_to_response
        resp = render_to_response('Hello {{ username }}!', {
            'username':     req.session['username']
        }, req)

    `render_to_string` and `render_to_response` take at least the name of
    the template as argument, then the optional dict which will become the
    context.  If you also provide a request object as third argument the
    context processors will be applied.

    `render_to_response` also takes a forth parameter which can be the
    content type which defaults to `DEFAULT_CONTENT_TYPE`.

    Converting Filters
    ==================

    One of the useful objects provided by `django.contrib.jinja` is the
    `register` object which can be used to register filters, tests and
    global objects.  You can also convert any filter django provides in
    a Jinja filter using `convert_django_filter`::

        from django.contrib.jinja import register, convert_django_filter
        from django.template.defaultfilters import floatformat

        register.filter(convert_django_filter(floatformat), 'floatformat')

    Available methods on the `register` object:

    ``object (obj[, name])``
        Register a new global as name or with the object's name.
        Returns the function object unchanged so that you can use
        it as decorator if no name is provided.

    ``filter (func[, name])``
        Register a function as filter with the name provided or
        the object's name as filtername.
        Returns the function object unchanged so that you can use
        it as decorator if no name is provided.

    ``test (func[, name])``
        Register a function as test with the name provided or the
        object's name as testname.
        Returns the function object unchanged so that you can use
        it as decorator if no name is provided.

    ``context_inclusion (func, template[, name])``
        Register a function with a name provided or the func object's
        name in the global namespace that acts as subrender function.

        func is called with the callers context as dict and the
        arguments and keywords argument of the inclusion function.
        The function should then process the context and return a
        new context or the same context object. Afterwards the
        template is rendered with this context.

        Example::

            def add_author(context, author=None):
                if author is not None:
                    author = Author.objects.get(name=author)
                context['author'] = author
                return context

            register.context_inclusion(add_author, 'author_details.html',
                                       'render_author_details')

        You can use it in the template like this then::

            {{ render_author_details('John Doe') }}

    ``clean_inclusion (func, template[, name[, run_processors]]) ``
        Works like `context_inclusion` but doesn't use the calles
        context but an empty context. If `run_processors` is `True`
        it will lookup the context for a `request` object and pass
        it to the render function to apply context processors.

    :copyright: 2007 by Armin Ronacher, Bryan McLemore.
    :license: BSD, see LICENSE for more details.
"""
try:
    __import__('django')
except ImportError:
    raise ImportError('installed django required for djangosupport')
else:
    from jinja.contrib._djangosupport import configure

__all__ = ['configure']
