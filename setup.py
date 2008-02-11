# -*- coding: utf-8 -*-
"""
jinja
~~~~~

Jinja is a `sandboxed`_ template engine written in pure Python. It
provides a `Django`_ like non-XML syntax and compiles templates into
executable python code. It's basically a combination of Django templates
and python code.

Nutshell
--------

Here a small example of a Jinja template::

    {% extends 'base.html' %}
    {% block title %}Memberlist{% endblock %}
    {% block content %}
      <ul>
      {% for user in users %}
        <li><a href="{{ user.url|e }}">{{ user.username|e }}</a></li>
      {% endfor %}
      </ul>
    {% endblock %}

Philosophy
----------

Application logic is for the controller but don't try to make the life
for the template designer too hard by giving him too few functionality.

For more informations visit the new `jinja webpage`_ and `documentation`_.

Note
----

This is the Jinja 1.0 release which is completely incompatible with the
old "pre 1.0" branch. The old branch will still receive security updates
and bugfixes but the 1.0 branch will be the only version that receives
support.

If you have an application that uses Jinja 0.9 and won't be updated in
the near future the best idea is to ship a Jinja 0.9 checkout together
with the application.

The `Jinja tip`_ is installable via `easy_install` with ``easy_install
Jinja==dev``.

.. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: http://www.djangoproject.com/
.. _jinja webpage: http://jinja.pocoo.org/
.. _documentation: http://jinja.pocoo.org/documentation/index.html
.. _Jinja tip: http://dev.pocoo.org/hg/jinja-main/archive/tip.tar.gz#egg=Jinja-dev
"""
import os
import sys
import ez_setup
ez_setup.use_setuptools()

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsError
from setuptools import setup, Extension, Feature


def list_files(path):
    for fn in os.listdir(path):
        if fn.startswith('.'):
            continue
        fn = os.path.join(path, fn)
        if os.path.isfile(fn):
            yield fn


class optional_build_ext(build_ext):

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsError, e:
            self.compiler = None
            self._setup_error = e

    def build_extension(self, ext):
        try:
            if self.compiler is None:
                raise self._setup_error
            build_ext.build_extension(self, ext)
        except CCompilerError, e:
            print '=' * 79
            print 'INFORMATION'
            print '  the speedup extension could not be compiled, Jinja will'
            print '  fall back to the native python classes.'
            print '=' * 79
        except:
            e = sys.exc_info()[1]
            print '=' * 79
            print 'WARNING'
            print '  could not compile optional speedup extension. This is'
            print '  is not a real problem because Jinja provides a native'
            print '  implementation of those classes but for best performance'
            print '  you could try to reinstall Jinja after fixing this'
            print '  problem: %s' % e
            print '=' * 79


setup(
    name='Jinja',
    version='1.3',
    url='http://jinja.pocoo.org/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A small but fast and easy to use stand-alone template '
                'engine written in pure python.',
    long_description = __doc__,
    # jinja is egg safe. But because we distribute the documentation
    # in form of html and txt files it's a better idea to extract the files
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    keywords=['python.templating.engines'],
    packages=['jinja', 'jinja.translators', 'jinja.contrib'],
    data_files=[
        ('docs/html', list(list_files('docs/html'))),
        ('docs/txt', list(list_files('docs/src')))
    ],
    entry_points='''
    [python.templating.engines]
    jinja = jinja.plugin:BuffetPlugin
    ''',
    extras_require={'plugin': ['setuptools>=0.6a2']},
    features={
        'speedups': Feature(
            'optional C-speed enhancements',
            standard=True,
            ext_modules=[
                Extension('jinja._speedups', ['jinja/_speedups.c'])
            ]
        ),
        'extended-debugger': Feature(
            'extended debugger',
            standard=True,
            ext_modules=[
                Extension('jinja._debugger', ['jinja/_debugger.c'])
            ]
        )
    },
    cmdclass={'build_ext': optional_build_ext}
)
