# -*- coding: utf-8 -*-
"""
    unit test for security features
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2.sandbox import SandboxedEnvironment, \
     ImmutableSandboxedEnvironment, unsafe


class PrivateStuff(object):

    def bar(self):
        return 23

    @unsafe
    def foo(self):
        return 42

    def __repr__(self):
        return 'PrivateStuff'


class PublicStuff(object):
    bar = lambda self: 23
    _foo = lambda self: 42

    def __repr__(self):
        return 'PublicStuff'


test_unsafe = '''
>>> env = MODULE.SandboxedEnvironment()
>>> env.from_string("{{ foo.foo() }}").render(foo=MODULE.PrivateStuff())
Traceback (most recent call last):
    ...
SecurityError: <bound method PrivateStuff.foo of PrivateStuff> is not safely callable
>>> env.from_string("{{ foo.bar() }}").render(foo=MODULE.PrivateStuff())
u'23'

>>> env.from_string("{{ foo._foo() }}").render(foo=MODULE.PublicStuff())
Traceback (most recent call last):
    ...
SecurityError: access to attribute '_foo' of 'PublicStuff' object is unsafe.
>>> env.from_string("{{ foo.bar() }}").render(foo=MODULE.PublicStuff())
u'23'

>>> env.from_string("{{ foo.__class__ }}").render(foo=42)
u''
>>> env.from_string("{{ foo.func_code }}").render(foo=lambda:None)
u''
>>> env.from_string("{{ foo.__class__.__subclasses__() }}").render(foo=42)
Traceback (most recent call last):
    ...
SecurityError: access to attribute '__class__' of 'int' object is unsafe.
'''


test_restricted = '''
>>> env = MODULE.SandboxedEnvironment()
>>> env.from_string("{% for item.attribute in seq %}...{% endfor %}")
Traceback (most recent call last):
    ...
TemplateSyntaxError: expected token 'in', got '.' (line 1)
>>> env.from_string("{% for foo, bar.baz in seq %}...{% endfor %}")
Traceback (most recent call last):
    ...
TemplateSyntaxError: expected token 'in', got '.' (line 1)
'''


test_immutable_environment = '''
>>> env = MODULE.ImmutableSandboxedEnvironment()
>>> env.from_string('{{ [].append(23) }}').render()
Traceback (most recent call last):
    ...
SecurityError: access to attribute 'append' of 'list' object is unsafe.
>>> env.from_string('{{ {1:2}.clear() }}').render()
Traceback (most recent call last):
    ...
SecurityError: access to attribute 'clear' of 'dict' object is unsafe.
'''
