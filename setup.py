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

For more informations visit the new `jinja2 webpage`_ and `documentation`_.

The `Jinja2 tip`_ is installable via `easy_install` with ``easy_install
Jinja2==dev``.

.. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: http://www.djangoproject.com/
.. _jinja webpage: http://jinja2.pocoo.org/
.. _documentation: http://jinja2.pocoo.org/documentation/index.html
.. _Jinja tip: http://dev.pocoo.org/hg/jinja2-main/archive/tip.tar.gz#egg=Jinja2-dev
"""
import os
import sys
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, Extension, Feature
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsPlatformError


def list_files(path):
    for fn in os.listdir(path):
        if fn.startswith('.'):
            continue
        fn = os.path.join(path, fn)
        if os.path.isfile(fn):
            yield fn


def get_terminal_width():
    """Return the current terminal dimensions."""
    try:
        from struct import pack, unpack
        from fcntl import ioctl
        from termios import TIOCGWINSZ
        s = pack('HHHH', 0, 0, 0, 0)
        return unpack('HHHH', ioctl(sys.stdout.fileno(), TIOCGWINSZ, s))[1]
    except:
        return 80


class optional_build_ext(build_ext):
    """This class allows C extension building to fail."""

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            self._unavailable()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except CCompilerError, x:
            self._unavailable()

    def _unavailable(self):
        width = get_terminal_width()
        print '*' * width
        print """WARNING:
An optional C extension could not be compiled, speedups will not be
available."""
        print '*' * width


setup(
    name='Jinja2',
    version='2.0dev',
    url='http://jinja.pocoo.org/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A small but fast and easy to use stand-alone template '
                'engine written in pure python.',
    long_description=__doc__,
    # jinja is egg safe. But because we distribute the documentation
    # in form of html and txt files it's a better idea to extract the files
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    packages=['jinja2'],
    data_files=[
        ('docs/html', list(list_files('docs/html'))),
        ('docs/txt', list(list_files('docs/src')))
    ],
    features={
        'speedups': Feature("optional C speed-enhancements",
            standard=True,
            ext_modules=[
                Extension('jinja2._speedups', ['jinja2/_speedups.c'])
            ]
        )
    },
    extras_require={'i18n': ['Babel>=0.8']},
    entry_points="""
    [babel.extractors]
    jinja2 = jinja.i18n:babel_extract[i18n]
    """
)
