# -*- coding: utf-8 -*-
try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass
from setuptools import setup


setup(
    name = 'Jinja',
    version = '0.9',
    url = 'http://wsgiarea.pocoo.org/jinja/',
    license = 'BSD',
    author = 'Armin Ronacher',
    author_email = 'armin.ronacher@active-4.com',
    description = 'A small but fast and easy to use stand-alone template engine written in pure python.',
    long_description = '''\
Jinja is a small but very fast and easy to use stand-alone template engine
written in pure Python.

Since version 0.6 it uses a new parser that increases parsing performance
a lot by caching the nodelists on disk if wanted.

It includes multiple template inheritance and other features like simple
value escaping.


Template Syntax
===============

This is a small example template in which you can see how Jinja's syntax
looks like::

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>My Webpage</title>
    </head
    <body>
        <ul id="navigation">
        {% for item in navigation %}
            <li><a href="{{ item.href }}">{{ item.caption|e }}</a></li>
        {% endfor %}
        </ul>

        <h1>My Webpage</h1>
        {{ variable }}
    </body>
    </html>


Usage
=====

Here is a small example::

    from jinja import Template, Context, FileSystemLoader

    t = Template('mytemplate', FileSystemLoader('/path/to/the/templates'))
    c = Context({
        'navigation' [
            {'href': '#', 'caption': 'Index'},
            {'href': '#', 'caption': 'Spam'}
        ],
        'variable': '<strong>hello world</strong>'
    })
    print t.render(c)


Unicode Support
===============

Jinja comes with built-in Unicode support. As a matter of fact, the return
value of ``Template.render()`` will be a Python unicode object.

You can still output ``str`` objects as well when you encode the result::

    s = t.render(c).encode('utf-8')

For more examples check out the `documentation`_ on the `jinja webpage`_.

.. _documentation: http://wsgiarea.pocoo.org/jinja/docs/
.. _jinja webpage: http://wsgiarea.pocoo.org/jinja/
''',
    keywords = 'wsgi web templateengine templates',
    packages = ['jinja'],
    platforms = 'any',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
