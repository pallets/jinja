# -*- coding: utf-8 -*-
"""
Jinja2
~~~~~~

Jinja2 is a template engine written in pure Python.  It provides a
`Django`_ inspired non-XML syntax but supports inline expressions and
an optional `sandboxed`_ environment.

Nutshell
--------

Here a small example of a Jinja template::

    {% extends 'base.html' %}
    {% block title %}Memberlist{% endblock %}
    {% block content %}
      <ul>
      {% for user in users %}
        <li><a href="{{ user.url }}">{{ user.username }}</a></li>
      {% endfor %}
      </ul>
    {% endblock %}

Philosophy
----------

Application logic is for the controller but don't try to make the life
for the template designer too hard by giving him too few functionality.

For more informations visit the new `Jinja2 webpage`_ and `documentation`_.

The `Jinja2 tip`_ is installable via `easy_install` with ``easy_install
Jinja2==dev``.

.. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: http://www.djangoproject.com/
.. _Jinja2 webpage: http://jinja.pocoo.org/
.. _documentation: http://jinja.pocoo.org/2/documentation/
.. _Jinja2 tip: http://dev.pocoo.org/hg/jinja2-main/archive/tip.tar.gz#egg=Jinja2-dev
"""
import os
import sys

from setuptools import setup, Extension, Feature

# tell distribute to use 2to3 with our own fixers.
extra = {}
if sys.version_info >= (3, 0):
    extra.update(
        use_2to3=True,
        use_2to3_fixers=['custom_fixers']
    )


setup(
    name='Jinja2',
    version='2.3.1',
    url='http://jinja.pocoo.org/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A small but fast and easy to use stand-alone template '
                'engine written in pure python.',
    long_description=__doc__,
    # jinja is egg safe. But we hate eggs
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    packages=['jinja2', 'jinja2.testsuite', 'jinja2.testsuite.res'],
    features={
        'speedups': Feature("optional C speed-enhancements",
            standard=False,
            ext_modules=[
                Extension('jinja2._speedups', ['jinja2/_speedups.c'])
            ]
        )
    },
    extras_require={'i18n': ['Babel>=0.8']},
    test_suite='jinja2.testsuite.suite',
    include_package_data=True,
    entry_points="""
    [babel.extractors]
    jinja2 = jinja2.ext:babel_extract[i18n]
    """,
    **extra
)
