Sandbox
=======

The Jinja2 sandbox can be used to evaluate untrusted code.  Access to unsafe
attributes and methods is prohibited.

Assuming `env` is a :class:`SandboxedEnvironment` in the default configuration
the following piece of code shows how it works:

>>> env.from_string("{{ func.func_code }}").render(func=lambda:None)
u''
>>> env.from_string("{{ func.func_code.do_something }}").render(func=lambda:None)
Traceback (most recent call last):
  ...
SecurityError: access to attribute 'func_code' of 'function' object is unsafe.


.. module:: jinja2.sandbox

.. autoclass:: SandboxedEnvironment([options])
    :members: is_safe_attribute, is_safe_callable

.. autoclass:: ImmutableSandboxedEnvironment([options])

.. autoexception:: SecurityError

.. autofunction:: unsafe

.. autofunction:: is_internal_attribute

.. autofunction:: modifies_builtin_mutable
