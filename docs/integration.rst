Integration
===========


Flask
-----

The `Flask`_ web application framework, also maintained by Pallets, uses
Jinja templates by default. Flask sets up a Jinja environment and
template loader for you, and provides functions to easily render
templates from view functions.

.. _Flask: https://flask.palletsprojects.com


Django
------

Django supports using Jinja as its template engine, see
https://docs.djangoproject.com/en/stable/topics/templates/#support-for-template-engines.


.. _babel-integration:

Babel
-----

Jinja provides support for extracting gettext messages from templates
via a `Babel`_ extractor entry point called
``jinja2.ext.babel_extract``. The support is implemented as part of the
:ref:`i18n-extension` extension.

Gettext messages are extracted from both ``trans`` tags and code
expressions.

To extract gettext messages from templates, the project needs a Jinja
section in its Babel extraction method `mapping file`_:

.. sourcecode:: ini

    [jinja2: **/templates/**.html]
    encoding = utf-8

The syntax related options of the :class:`Environment` are also
available as configuration values in the mapping file. For example, to
tell the extractor that templates use ``%`` as
``line_statement_prefix`` you can use this code:

.. sourcecode:: ini

    [jinja2: **/templates/**.html]
    encoding = utf-8
    line_statement_prefix = %

:ref:`jinja-extensions` may also be defined by passing a comma separated
list of import paths as the ``extensions`` value. The i18n extension is
added automatically.

Template syntax errors are ignored by default. The assumption is that
tests will catch syntax errors in templates. If you don't want to ignore
errors, add ``silent = false`` to the settings.

.. _Babel: https://babel.readthedocs.io/
.. _mapping file: https://babel.readthedocs.io/en/latest/messages.html#extraction-method-mapping-and-configuration


Pylons
------

It's easy to integrate Jinja into a `Pylons`_ application.

The template engine is configured in ``config/environment.py``. The
configuration for Jinja looks something like this:

.. code-block:: python

    from jinja2 import Environment, PackageLoader
    config['pylons.app_globals'].jinja_env = Environment(
        loader=PackageLoader('yourapplication', 'templates')
    )

After that you can render Jinja templates by using the ``render_jinja``
function from the ``pylons.templating`` module.

Additionally it's a good idea to set the Pylons ``c`` object to strict
mode. By default attribute access on missing attributes on the ``c``
object returns an empty string and not an undefined object. To change
this add this to ``config/environment.py``:

.. code-block:: python

    config['pylons.strict_c'] = True

.. _Pylons: https://pylonsproject.org/


Litestar
--------

`Litestar`_ allows you to easily render templates using a built-in templating engines,
including Jinja, and integrates it seamlessly into the framework.

To use Jinja templates with Litestar, you can register it through the
`template_config` parameter when creating an instance of the `Litestar`
application. Here's an example of how to set it up:

.. code-block:: python

    from pathlib import Path
    from litestar import Litestar
    from litestar.contrib.jinja import JinjaTemplateEngine
    from litestar.template.config import TemplateConfig

    app = Litestar(
        route_handlers=[],
        template_config=TemplateConfig(
            directory=Path("templates"),
            engine=JinjaTemplateEngine,
        ),
    )

This setup will allow you to use Jinja templates for rendering views in
your Litestar app. The `directory` specifies where the template files are
located, and the `engine` specifies which template engine to use, in this
case, `JinjaTemplateEngine`.

.. _Litestar: https://docs.litestar.dev/latest/usage/templating.html#registering-a-template-engine
