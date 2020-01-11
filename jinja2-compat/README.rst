The Jinja2 package has been renamed to `Jinja`_. This package provides
compatibility while projects transition to the new name. Imports from
``jinja2`` will be redirected to ``jinja`` and a deprecation warning
will be emitted.

Projects are advised to require 'Jinja' instead of 'Jinja2' and replace
all imports of ``jinja2`` with ``jinja`` to continue receiving updates.

.. _Jinja: https://pypi.org/project/Jinja/
