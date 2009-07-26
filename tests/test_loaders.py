# -*- coding: utf-8 -*-
"""
    unit test for the loaders
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

import time
import tempfile
from jinja2 import Environment, loaders
from jinja2.loaders import split_template_path
from jinja2.exceptions import TemplateNotFound

from nose.tools import assert_raises


dict_loader = loaders.DictLoader({
    'justdict.html':        'FOO'
})
package_loader = loaders.PackageLoader('loaderres', 'templates')
filesystem_loader = loaders.FileSystemLoader('loaderres/templates')
function_loader = loaders.FunctionLoader({'justfunction.html': 'FOO'}.get)
choice_loader = loaders.ChoiceLoader([dict_loader, package_loader])
prefix_loader = loaders.PrefixLoader({
    'a':        filesystem_loader,
    'b':        dict_loader
})


def test_dict_loader():
    env = Environment(loader=dict_loader)
    tmpl = env.get_template('justdict.html')
    assert tmpl.render().strip() == 'FOO'
    assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def test_package_loader():
    env = Environment(loader=package_loader)
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def test_filesystem_loader():
    env = Environment(loader=filesystem_loader)
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    tmpl = env.get_template('foo/test.html')
    assert tmpl.render().strip() == 'FOO'
    assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def test_choice_loader():
    env = Environment(loader=choice_loader)
    tmpl = env.get_template('justdict.html')
    assert tmpl.render().strip() == 'FOO'
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def test_function_loader():
    env = Environment(loader=function_loader)
    tmpl = env.get_template('justfunction.html')
    assert tmpl.render().strip() == 'FOO'
    assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def test_prefix_loader():
    env = Environment(loader=prefix_loader)
    tmpl = env.get_template('a/test.html')
    assert tmpl.render().strip() == 'BAR'
    tmpl = env.get_template('b/justdict.html')
    assert tmpl.render().strip() == 'FOO'
    assert_raises(TemplateNotFound, env.get_template, 'missing')


def test_caching():
    changed = False
    class TestLoader(loaders.BaseLoader):
        def get_source(self, environment, template):
            return u'foo', None, lambda: not changed
    env = Environment(loader=TestLoader(), cache_size=-1)
    tmpl = env.get_template('template')
    assert tmpl is env.get_template('template')
    changed = True
    assert tmpl is not env.get_template('template')
    changed = False

    env = Environment(loader=TestLoader(), cache_size=0)
    assert env.get_template('template') \
           is not env.get_template('template')

    env = Environment(loader=TestLoader(), cache_size=2)
    t1 = env.get_template('one')
    t2 = env.get_template('two')
    print env.cache
    assert t2 is env.get_template('two')
    assert t1 is env.get_template('one')
    t3 = env.get_template('three')
    assert 'one' in env.cache
    assert 'two' not in env.cache
    assert 'three' in env.cache


def test_split_template_path():
    assert split_template_path('foo/bar') == ['foo', 'bar']
    assert split_template_path('./foo/bar') == ['foo', 'bar']
    assert_raises(TemplateNotFound, split_template_path, '../foo')
