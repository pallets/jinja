import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import jdebug
from jinja2 import Environment, DictLoader
from jinja2.exceptions import TemplateNotFound
from wsgiref.simple_server import make_server

e = Environment(loader=DictLoader({
    '/': u'''
<html>
  <head>
    <title>Various Broken Templates</title>
    <style type="text/css">
      body {
        margin: 2em;
        font-size: 1.5em;
        font-family: sans-serif
      }
      a {
        color: #d00;
      }
    </style>
  </head>
  <body>
    <h1>Various Broken Templates</h1>
    <p>
      This small WSGI application serves some Jinja templates that
      are just broken. It uses the colubrid traceback middleware to
      render those errors including source code.
    </p>
    <ul>
      <li><a href="syntax_error">syntax error</a></li>
      <li><a href="runtime_error">runtime error</a></li>
      <li><a href="nested_syntax_error">nested syntax error</a></li>
      <li><a href="nested_runtime_error">nested runtime error</a></li>
      <li><a href="code_runtime_error">runtime error in code</a></li>
      <li><a href="syntax_from_string">a syntax error from string</a></li>
      <li><a href="runtime_from_string">runtime error from a string</a></li>
      <li><a href="multiple_templates">multiple templates</a></li>
    </ul>
  </body>
</html>
''',
    '/syntax_error': u'''
{% for item in foo %}
    ...
{% endif %}
    ''',
    '/runtime_error': u'''
{% set foo = 1 / 0 %}
    ''',
    '/nested_runtime_error': u'''
{% include 'runtime_broken' %}
    ''',
    '/nested_syntax_error': u'''
{% include 'syntax_broken' %}
    ''',
    '/code_runtime_error': u'''We have a runtime error here:
    {{ broken() }}''',
    '/multiple_templates': '''\
{{ fire_multiple_broken() }}
''',

    'runtime_broken': '''\
This is an included template
{% set a = 1 / 0 %}''',
    'syntax_broken': '''\
This is an included template
{% raw %}just some foo''',
    'multiple_broken': '''\
Just some context:
{% include 'macro_broken' %}
{{ broken() }}
''',
    'macro_broken': '''\
{% macro broken %}
    {{ 1 / 0 }}
{% endmacro %}
'''
}))
e.globals['fire_multiple_broken'] = lambda: \
    e.get_template('multiple_broken').render()

FAILING_STRING_TEMPLATE = '{{ 1 / 0 }}'
BROKEN_STRING_TEMPLATE = '{% if foo %}...{% endfor %}'


def broken():
    raise RuntimeError("I'm broken")


def test(environ, start_response):
    path = environ.get('PATH_INFO' or '/')
    try:
        tmpl = e.get_template(path)
    except TemplateNotFound:
        if path == '/syntax_from_string':
            tmpl = e.from_string(BROKEN_STRING_TEMPLATE)
        elif path == '/runtime_from_string':
            tmpl = e.from_string(FAILING_STRING_TEMPLATE)
        else:
            start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
            return ['NOT FOUND']
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [tmpl.render(broken=broken).encode('utf-8')]


if __name__ == '__main__':
    from werkzeug.debug import DebuggedApplication
    app = DebuggedApplication(test, True)
    make_server("localhost", 7000, app).serve_forever()
