# -*- coding: utf-8 -*-
import jinja
import os
import ez_setup
ez_setup.use_setuptools()
from setuptools import setup
from inspect import getdoc


def list_files(path):
    for fn in os.listdir(path):
        if fn.startswith('.'):
            continue
        fn = os.path.join(path, fn)
        if os.path.isfile(fn):
            yield fn


setup(
    name = 'Jinja',
    version = '1.0',
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
    platforms = 'any',
    entry_points='''
    [python.templating.engines]
    jinja = jinja.plugin:BuffetPlugin
    ''',
    extras_require = {'plugin': ['setuptools>=0.6a2']}
)
