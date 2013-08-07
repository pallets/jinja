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

.. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: http://www.djangoproject.com/
.. _Jinja2 webpage: http://jinja.pocoo.org/
.. _documentation: http://jinja.pocoo.org/2/documentation/
"""
import sys

from setuptools import setup


# ignore the old '--with-speedups' flag
try:
    speedups_pos = sys.argv.index('--with-speedups')
except ValueError:
    pass
else:
    del sys.argv[speedups_pos]
    sys.stderr.write('*' * 74 + '\n')
    sys.stderr.write('WARNING:\n')
    sys.stderr.write('  the --with-speedups flag is deprecated\n')
    sys.stderr.write('  For the actual speedups install the MarkupSafe '
                     'package.\n')
    sys.stderr.write('*' * 74 + '\n')


setup(
    name='Jinja2',
    version='2.7.1',
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
    install_requires=['markupsafe'],
    extras_require={'i18n': ['Babel>=0.8']},
    test_suite='jinja2.testsuite.suite',
    include_package_data=True,
    entry_points="""
    [babel.extractors]
    jinja2 = jinja2.ext:babel_extract[i18n]
    """
)
