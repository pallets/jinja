# -*- coding: utf-8 -*-
"""
    unit test for the loaders
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import time
import tempfile
from jinja import Environment, loaders
from jinja.exceptions import TemplateNotFound


dict_loader = loaders.DictLoader({
    'justdict.html':        'FOO'
})

package_loader = loaders.PackageLoader('loaderres', 'templates')

filesystem_loader = loaders.FileSystemLoader('loaderres/templates')

memcached_loader = loaders.MemcachedFileSystemLoader('loaderres/templates')

function_loader = loaders.FunctionLoader({'justfunction.html': 'FOO'}.get)

choice_loader = loaders.ChoiceLoader([dict_loader, package_loader])


class FakeLoader(loaders.BaseLoader):
    local_attr = 42


def test_dict_loader():
    env = Environment(loader=dict_loader)
    tmpl = env.get_template('justdict.html')
    assert tmpl.render().strip() == 'FOO'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')


def test_package_loader():
    env = Environment(loader=package_loader)
    for x in xrange(2):
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        try:
            env.get_template('missing.html')
        except TemplateNotFound:
            pass
        else:
            raise AssertionError('expected template exception')

        # second run in native mode (no pkg_resources)
        package_loader.force_native = True
        del package_loader._load_func


def test_filesystem_loader():
    env = Environment(loader=filesystem_loader)
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    tmpl = env.get_template('foo/test.html')
    assert tmpl.render().strip() == 'FOO'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')


def test_memcached_loader():
    env = Environment(loader=memcached_loader)
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    tmpl = env.get_template('foo/test.html')
    assert tmpl.render().strip() == 'FOO'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')


def test_choice_loader():
    env = Environment(loader=choice_loader)
    tmpl = env.get_template('justdict.html')
    assert tmpl.render().strip() == 'FOO'
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')

    # this should raise an TemplateNotFound error with the
    # correct name
    try:
        env.get_template('brokenimport.html')
    except TemplateNotFound, e:
        assert e.name == 'missing.html'
    else:
        raise AssertionError('expected exception')


def test_function_loader():
    env = Environment(loader=function_loader)
    tmpl = env.get_template('justfunction.html')
    assert tmpl.render().strip() == 'FOO'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')


def test_loader_redirect():
    env = Environment(loader=FakeLoader())
    assert env.loader.local_attr == 42
    assert env.loader.get_source
    assert env.loader.load


class MemcacheTestingLoader(loaders.CachedLoaderMixin, loaders.BaseLoader):

    def __init__(self, enable):
        loaders.CachedLoaderMixin.__init__(self, enable, 40, None, True, 'foo')
        self.times = {}
        self.idx = 0

    def touch(self, name):
        self.times[name] = time.time()

    def get_source(self, environment, name, parent):
        self.touch(name)
        self.idx += 1
        return 'Template %s (%d)' % (name, self.idx)

    def check_source_changed(self, environment, name):
        if name in self.times:
            return self.times[name]
        return -1


memcache_env = Environment(loader=MemcacheTestingLoader(True))
no_memcache_env = Environment(loader=MemcacheTestingLoader(False))


test_memcaching = r'''
>>> not_caching = MODULE.no_memcache_env.loader
>>> caching = MODULE.memcache_env.loader
>>> touch = caching.touch

>>> tmpl1 = not_caching.load('test.html')
>>> tmpl2 = not_caching.load('test.html')
>>> tmpl1 == tmpl2
False

>>> tmpl1 = caching.load('test.html')
>>> tmpl2 = caching.load('test.html')
>>> tmpl1 == tmpl2
True

>>> touch('test.html')
>>> tmpl2 = caching.load('test.html')
>>> tmpl1 == tmpl2
False
'''
