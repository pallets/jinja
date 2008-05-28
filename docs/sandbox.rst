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

.. autofunction:: modifies_known_mutable

.. admonition:: Note

    The Jinja2 sandbox alone is no solution for perfect security.  Especially
    for web applications you have to keep in mind that users may create
    templates with arbitrary HTML in so it's crucial to ensure that (if you
    are running multiple users on the same server) they can't harm each other
    via JavaScript insertions and much more.

    Also the sandbox is only as good as the configuration.  We stronly
    recommend only passing non-shared resources to the template and use
    some sort of whitelisting for attributes.

    Also keep in mind that templates may raise runtime or compile time errors,
    so make sure to catch them.
