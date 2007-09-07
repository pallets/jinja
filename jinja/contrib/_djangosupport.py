# -*- coding: utf-8 -*-
"""
    jinja.contrib._djangosupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Django suport layer. This module is a metamodule, do never import it
    directly or access any of the functions defined here.

    The public interface is `jinja.contrib.djangosupport` and
    `django.contrib.jinja`. See the docstring of `jinja.contrib.djangosupport`
    for more details.

    :copyright: 2007 by Armin Ronacher, Bryan McLemore.
    :license: BSD, see LICENSE for more details.
"""
import sys
import new
from django.conf import settings
from django.template.context import get_standard_processors
from django.http import HttpResponse
from django import contrib

from jinja import Environment, FileSystemLoader, ChoiceLoader
from jinja.loaders import MemcachedFileSystemLoader


exported = ['render_to_response', 'render_to_string', 'convert_django_filter']


#: used environment
env = None


#: default filters
DEFAULT_FILTERS = [
    'django.template.defaultfilters.date',
    'django.template.defaultfilters.timesince',
    'django.template.defaultfilters.linebreaks',
    'django.contrib.humanize.templatetags.humanize.intcomma'
]


def configure(convert_filters=DEFAULT_FILTERS, loader=None, **options):
    """
    Initialize the system.
    """
    global env

    if env is not None:
        raise RuntimeError('jinja already configured')

    # setup environment
    if loader is None:
        loaders = [FileSystemLoader(l) for l in settings.TEMPLATE_DIRS]
        if not loaders:
            loader = None
        elif len(loaders) == 1:
            loader = loaders[0]
        else:
            loader = ChoiceLoader(loaders)
    env = Environment(loader=loader, **options)

    # convert requested filters
    for name in convert_filters:
        env.filters[name] = convert_django_filter(name)

    # import templatetags of installed apps
    for app in settings.INSTALLED_APPS:
        try:
            __import__(app + '.templatetags')
        except ImportError:
            pass

    # setup the django.contrib.jinja module
    setup_django_module()


def setup_django_module():
    """
    create a new Jinja module for django.
    """
    from jinja.contrib import djangosupport
    module = contrib.jinja = sys.modules['django.contrib.jinja'] = \
             new.module('django.contrib.jinja')
    module.env = env
    module.__doc__ = djangosupport.__doc__
    module.register = Library()
    public_names = module.__all__ = ['register', 'env']
    get_name = globals().get
    for name in exported:
        setattr(module, name, get_name(name))
        public_names.append(name)


def render_to_response(template, context={}, request=None,
                       mimetype=None):
    """This function will take a few variables and spit out a full webpage."""
    content = render_to_string(template, context, request)
    if mimetype is None:
        mimetype = settings.DEFUALT_CONTENT_TYPE
    return HttpResponse(content, content_type)


def render_to_string(template, context={}, request=None):
    """Render a template to a string."""
    assert env is not None, 'Jinja not configured for django'
    if request is not None:
        context['request'] = request
        for processor in get_standard_processors():
            context.update(processor(request))
    template = env.get_template(template)
    return template.render(context)


def convert_django_filter(f):
    """Convert a django filter into a Jinja filter."""
    if isinstance(f, str):
        p = f.split('.')
        f = getattr(__import__('.'.join(p[:-1]), None, None, ['']), p[-1])
    def filter_factory(*args):
        def wrapped(env, ctx, value):
            return f(value, *args)
        return wrapped
    try:
        filter_factory.__name__ = f.__name__
        filter_factory.__doc__ = f.__doc__
    except:
        pass
    return filter_factory


class Library(object):
    """
    Continues a general feel of wrapping all the registration
    methods for easy importing.

    This is available in `django.contrib.jinja` as `register`.

    For more details see the docstring of the `django.contrib.jinja` module.
    """
    __slots__ = ()

    def object(obj, name=None):
        """Register a new global."""
        if name is None:
            name = getattr(obj, '__name__')
        env.globals[name] = obj
        return func

    def filter(func, name=None):
        """Register a new filter function."""
        if name is None:
            name = func.__name__
        env.filters[name] = func
        return func

    def test(func, name):
        """Register a new test function."""
        if name is None:
            name = func.__name__
        env.tests[name] = func
        return func

    def context_inclusion(func, template, name=None):
        """
        Similar to the inclusion tag from django this one expects func to be a
        function with a similar argument list to func(context, *args, **kwargs)

        It passed in the current context allowing the function to edit it or read
        from it.  the function must return a dict with which to pass into the
        renderer.  Normally expected is an altered dictionary.

        Note processors are NOT ran on this context.
        """
        def wrapper(env, context, *args, **kwargs):
            context = func(context.to_dict(), *args, **kwargs)
            return render_to_string(template, context)
        wrapper.jinja_context_callable = True
        if name is None:
            name = func.__name__
        try:
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
        except:
            pass
        env.globals[name] = wrapper

    def clean_inclusion(func, template, name=None, run_processors=False):
        """
        Similar to above however it won't pass the context into func().
        Also the returned context will have the context processors run upon it.
        """
        def wrapper(env, context, *args, **kwargs):
            if run_processors:
                request = context['request']
            else:
                request = None
            context = func({}, *args, **kwargs)
            return render_to_string(template, context, request)
        wrapper.jinja_context_callable = True
        if name is None:
            name = func.__name__
        try:
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
        except:
            pass
        env.globals[name] = wrapper
