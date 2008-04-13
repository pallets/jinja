# -*- coding: utf-8 -*-
"""
    unit test for the undefined singletons
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import Environment
from jinja2.exceptions import TemplateRuntimeError
from jinja2.datastructure import SilentUndefined, ComplainingUndefined


silent_env = Environment(undefined_singleton=SilentUndefined)
complaining_env = Environment(undefined_singleton=ComplainingUndefined)


JUSTUNDEFINED = '''{{ missing }}'''
DEFINEDUNDEFINED = '''{{ missing is defined }}|{{ given is defined }}'''
ITERATION = '''{% for item in missing %}{{ item }}{% endfor %}'''
CONCATENATION = '''{{ missing + [1, 2] + missing + [3] }}'''


def test_silent_defined():
    tmpl = silent_env.from_string(DEFINEDUNDEFINED)
    assert tmpl.render(given=0) == 'False|True'


def test_complaining_defined():
    tmpl = complaining_env.from_string(DEFINEDUNDEFINED)
    assert tmpl.render(given=0) == 'False|True'


def test_silent_rendering():
    tmpl = silent_env.from_string(JUSTUNDEFINED)
    assert tmpl.render() == ''


def test_complaining_undefined():
    tmpl = complaining_env.from_string(JUSTUNDEFINED)
    try:
        tmpl.render()
    except TemplateRuntimeError:
        pass
    else:
        raise ValueError('template runtime error expected')


def test_silent_iteration():
    tmpl = silent_env.from_string(ITERATION)
    assert tmpl.render() == ''


def test_complaining_iteration():
    tmpl = complaining_env.from_string(ITERATION)
    try:
        tmpl.render()
    except TemplateRuntimeError:
        pass
    else:
        raise ValueError('template runtime error expected')


def test_concatenation():
    tmpl = silent_env.from_string(CONCATENATION)
    assert tmpl.render() == '[1, 2, 3]'
