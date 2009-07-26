# -*- coding: utf-8 -*-
"""
    unit test for the undefined types
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Template
from jinja2.exceptions import UndefinedError

from nose.tools import assert_raises


def test_default_undefined():
    '''
>>> from jinja2 import Environment, Undefined
>>> env = Environment(undefined=Undefined)
>>> env.from_string('{{ missing }}').render()
u''
>>> env.from_string('{{ missing.attribute }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
>>> env.from_string('{{ missing|list }}').render()
u'[]'
>>> env.from_string('{{ missing is not defined }}').render()
u'True'
>>> env.from_string('{{ foo.missing }}').render(foo=42)
u''
>>> env.from_string('{{ not missing }}').render()
u'True'
'''

def test_debug_undefined():
    '''
>>> from jinja2 import Environment, DebugUndefined
>>> env = Environment(undefined=DebugUndefined)
>>> env.from_string('{{ missing }}').render()
u'{{ missing }}'
>>> env.from_string('{{ missing.attribute }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
>>> env.from_string('{{ missing|list }}').render()
u'[]'
>>> env.from_string('{{ missing is not defined }}').render()
u'True'
>>> env.from_string('{{ foo.missing }}').render(foo=42)
u"{{ no such element: int['missing'] }}"
>>> env.from_string('{{ not missing }}').render()
u'True'
'''

def test_strict_undefined():
    '''
>>> from jinja2 import Environment, StrictUndefined
>>> env = Environment(undefined=StrictUndefined)
>>> env.from_string('{{ missing }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
>>> env.from_string('{{ missing.attribute }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
>>> env.from_string('{{ missing|list }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
>>> env.from_string('{{ missing is not defined }}').render()
u'True'
>>> env.from_string('{{ foo.missing }}').render(foo=42)
Traceback (most recent call last):
  ...
UndefinedError: 'int' object has no attribute 'missing'
>>> env.from_string('{{ not missing }}').render()
Traceback (most recent call last):
  ...
UndefinedError: 'missing' is undefined
'''


def test_indexing_gives_undefined():
    t = Template("{{ var[42].foo }}")
    assert_raises(UndefinedError, t.render, var=0)
