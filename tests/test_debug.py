# -*- coding: utf-8 -*-
"""
    Test debug interface
    ~~~~~~~~~~~~~~~~~~~~

    Tests the traceback rewriter.

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD.
"""
from jinja2 import Environment
from test_loaders import filesystem_loader

env = Environment(loader=filesystem_loader)


def test_runtime_error():
    '''
>>> tmpl = env.get_template('broken.html')
>>> tmpl.render(fail=lambda: 1 / 0)
Traceback (most recent call last):
  File "loaderres/templates/broken.html", line 2, in top-level template code
    {{ fail() }}
  File "<doctest test_runtime_error[1]>", line 1, in <lambda>
    tmpl.render(fail=lambda: 1 / 0)
ZeroDivisionError: integer division or modulo by zero
'''


def test_syntax_error():
    '''
>>> tmpl = env.get_template('syntaxerror.html')
Traceback (most recent call last):
  ...
TemplateSyntaxError: unknown tag 'endif'
  File "loaderres/templates\\syntaxerror.html", line 4
    {% endif %}
'''


def test_regular_syntax_error():
    '''
>>> from jinja2.exceptions import TemplateSyntaxError
>>> raise TemplateSyntaxError('wtf', 42)
Traceback (most recent call last):
  ...
  File "<doctest test_regular_syntax_error[1]>", line 1, in <module>
    raise TemplateSyntaxError('wtf', 42)
TemplateSyntaxError: wtf
  line 42
'''
