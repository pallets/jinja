# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Configuration and Fixtures for the tests

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import pytest
import os

import warnings
warnings.simplefilter('error', DeprecationWarning)


def pytest_ignore_collect(path, config):
    from jinja2.utils import have_async_gen
    if 'async' in path.basename and not have_async_gen:
        return True
    return False


@pytest.fixture
def env():
    '''returns a new environment.
    '''
    from jinja2 import Environment
    return Environment()


@pytest.fixture
def dict_loader():
    '''returns DictLoader
    '''
    from jinja2.loaders import DictLoader
    return DictLoader({
        'justdict.html':        'FOO'
    })


@pytest.fixture
def package_loader():
    '''returns PackageLoader initialized from templates
    '''
    from jinja2.loaders import PackageLoader
    return PackageLoader('res', 'templates')


@pytest.fixture
def filesystem_loader():
    '''returns FileSystemLoader initialized to res/templates directory
    '''
    from jinja2.loaders import FileSystemLoader
    here = os.path.dirname(os.path.abspath(__file__))
    return FileSystemLoader(here + '/res/templates')


@pytest.fixture
def function_loader():
    '''returns a FunctionLoader
    '''
    from jinja2.loaders import FunctionLoader
    return FunctionLoader({'justfunction.html': 'FOO'}.get)


@pytest.fixture
def choice_loader(dict_loader, package_loader):
    '''returns a ChoiceLoader
    '''
    from jinja2.loaders import ChoiceLoader
    return ChoiceLoader([dict_loader, package_loader])


@pytest.fixture
def prefix_loader(filesystem_loader, dict_loader):
    '''returns a PrefixLoader
    '''
    from jinja2.loaders import PrefixLoader
    return PrefixLoader({
        'a':        filesystem_loader,
        'b':        dict_loader
    })
