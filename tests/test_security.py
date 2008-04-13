# -*- coding: utf-8 -*-
"""
    unit test for security features
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment


NONLOCALSET = '''\
{% for item in range(10) %}
    {%- set outer = item! -%}
{% endfor -%}
{{ outer }}'''


class PrivateStuff(object):
    bar = lambda self: 23
    foo = lambda self: 42
    foo.jinja_unsafe_call = True


class PublicStuff(object):
    jinja_allowed_attributes = ['bar']
    bar = lambda self: 23
    foo = lambda self: 42


test_unsafe = '''
>>> env.from_string("{{ foo.foo() }}").render(foo=MODULE.PrivateStuff())
u''
>>> env.from_string("{{ foo.bar() }}").render(foo=MODULE.PrivateStuff())
u'23'

>>> env.from_string("{{ foo.foo() }}").render(foo=MODULE.PublicStuff())
u''
>>> env.from_string("{{ foo.bar() }}").render(foo=MODULE.PublicStuff())
u'23'

>>> env.from_string("{{ foo.__class__ }}").render(foo=42)
u''

>>> env.from_string("{{ foo.func_code }}").render(foo=lambda:None)
u''
'''


test_restricted = '''
>>> env.from_string("{% for item.attribute in seq %}...{% endfor %}")
Traceback (most recent call last):
    ...
TemplateSyntaxError: cannot assign to expression (line 1)
>>> env.from_string("{% for foo, bar.baz in seq %}...{% endfor %}")
Traceback (most recent call last):
    ...
TemplateSyntaxError: cannot assign to expression (line 1)
'''


def test_nonlocal_set():
    env = Environment()
    env.globals['outer'] = 42
    tmpl = env.from_string(NONLOCALSET)
    assert tmpl.render() == '9'
    assert env.globals['outer'] == 42
