.. module:: jinja2.nativetypes

.. _nativetypes:

Native Python Types
===================

The default :class:`~jinja2.Environment` renders templates to strings. With
:class:`NativeEnvironment`, rendering a template produces a native Python type.
This is useful if you are using Jinja outside the context of creating text
files. For example, your code may have an intermediate step where users may use
templates to define values that will then be passed to a traditional string
environment.

Examples
--------

Adding two values results in an integer, not a string with a number:

>>> env = NativeEnvironment()
>>> t = env.from_string('{{ x + y }}')
>>> result = t.render(x=4, y=2)
>>> print(result)
6
>>> print(type(result))
int

Rendering list syntax produces a list:

>>> t = env.from_string('[{% for item in data %}{{ item + 1 }},{% endfor %}]')
>>> result = t.render(data=range(5))
>>> print(result)
[1, 2, 3, 4, 5]
>>> print(type(result))
list

Rendering something that doesn't look like a Python literal produces a string:

>>> t = env.from_string('{{ x }} * {{ y }}')
>>> result = t.render(x=4, y=2)
>>> print(result)
4 * 2
>>> print(type(result))
str

Rendering a Python object produces that object as long as it is the only node:

>>> class Foo:
...     def __init__(self, value):
...         self.value = value
...
>>> result = env.from_string('{{ x }}').render(x=Foo(15))
>>> print(type(result).__name__)
Foo
>>> print(result.value)
15

API
---

.. autoclass:: NativeEnvironment([options])

.. autoclass:: NativeTemplate([options])
    :members: render
