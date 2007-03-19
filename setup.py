# -*- coding: utf-8 -*-
try:
    import ez_setup
    ez_setup.use_setuptools()
except ImportError:
    pass
from setuptools import setup


setup(
    name = 'Jinja',
    version = '1.0',
    url = 'http://jinja.pocoo.org/',
    license = 'BSD',
    author = 'Armin Ronacher',
    author_email = 'armin.ronacher@active-4.com',
    description = 'A small but fast and easy to use stand-alone template '
                  'engine written in pure python.',
    zip_safe = True,
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
    extras_require = {'plugin': ['setuptools>=0.6a2']},
    entry_points='''
    [python.templating.engines]
    jinja = jinja.plugin:JinjaPlugin[plugin]
    '''
)
