# -*- coding: utf-8 -*-
"""
    Test debug interface
    ~~~~~~~~~~~~~~~~~~~~

    Tests the traceback rewriter.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from jinja2 import Environment
from test_loaders import filesystem_loader


env = Environment(loader=filesystem_loader)


test_runtime_error = '''
>>> tmpl = MODULE.env.get_template('broken.html')
>>> tmpl.render(fail=lambda: 1 / 0)
Traceback (most recent call last):
  File "loaderres/templates/broken.html", line 2, in top-level template code
    {{ fail() }}
  File "<doctest test_runtime_error[1]>", line 1, in <lambda>
    tmpl.render(fail=lambda: 1 / 0)
ZeroDivisionError: integer division or modulo by zero
'''


test_syntax_error = '''
>>> tmpl = MODULE.env.get_template('syntaxerror.html')
Traceback (most recent call last):
  ...
  File "loaderres/templates/syntaxerror.html", line 4, in <module>
    {% endif %}
TemplateSyntaxError: unknown tag 'endif' (syntaxerror.html, line 4)
'''
