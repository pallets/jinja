# -*- coding: utf-8 -*-
"""
    unit test for the loaders
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from jinja import Environment, loaders
from jinja.exceptions import TemplateNotFound


dict_loader = loaders.DictLoader({
    'justdict.html':        'FOO'
})

package_loader = loaders.PackageLoader('loaderres', 'templates')

filesystem_loader = loaders.FileSystemLoader('loaderres/templates')

function_loader = loaders.FunctionLoader({'justfunction.html': 'FOO'}.get)

choice_loader = loaders.ChoiceLoader([dict_loader, package_loader])


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
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
    try:
        env.get_template('missing.html')
    except TemplateNotFound:
        pass
    else:
        raise AssertionError('expected template exception')


def test_filesystem_loader():
    env = Environment(loader=filesystem_loader)
    tmpl = env.get_template('test.html')
    assert tmpl.render().strip() == 'BAR'
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
