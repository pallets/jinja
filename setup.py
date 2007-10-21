# -*- coding: utf-8 -*-
import jinja
import os
import sys
import ez_setup
ez_setup.use_setuptools()

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsError
from setuptools import setup, Extension, Feature
from inspect import getdoc


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
    name = 'Jinja',
    version = '1.2',
    url = 'http://jinja.pocoo.org/',
    license = 'BSD',
    author = 'Armin Ronacher',
    author_email = 'armin.ronacher@active-4.com',
    description = 'A small but fast and easy to use stand-alone template '
                  'engine written in pure python.',
    long_description = getdoc(jinja),
    # jinja is egg safe. But because we distribute the documentation
    # in form of html and txt files it's a better idea to extract the files
    zip_safe = False,
    classifiers = [
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
    keywords = ['python.templating.engines'],
    packages = ['jinja', 'jinja.translators'],
    data_files = [
        ('docs', list(list_files('docs/build'))),
        ('docs/txt', list(list_files('docs/src')))
    ],
    entry_points='''
    [python.templating.engines]
    jinja = jinja.plugin:BuffetPlugin
    ''',
    extras_require = {'plugin': ['setuptools>=0.6a2']},
    features = {
        'speedups': Feature(
            'optional C-speed enhancements',
            standard = True,
            ext_modules = [
                Extension('jinja._speedups', ['jinja/_speedups.c'])
            ]
        ),
        'extended-debugger': Feature(
            'extended debugger',
            standard = True,
            ext_modules = [
                Extension('jinja._debugger', ['jinja/_debugger.c'])
            ]
        )
    },
    cmdclass = {'build_ext': optional_build_ext}
)
