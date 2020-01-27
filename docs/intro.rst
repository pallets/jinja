Introduction
============

Jinja is a fast, expressive, extensible templating engine. Special
placeholders in the template allow writing code similar to Python
syntax. Then the template is passed data to render the final document.

It includes:

-   Template inheritance and inclusion.
-   Define and import macros within templates.
-   HTML templates can use autoescaping to prevent XSS from untrusted
    user input.
-   A sandboxed environment can safely render untrusted templates.
-   AsyncIO support for generating templates and calling async
    functions.
-   I18N support with Babel.
-   Templates are compiled to optimized Python code just-in-time and
    cached, or can be compiled ahead-of-time.
-   Exceptions point to the correct line in templates to make debugging
    easier.
-   Extensible filters, tests, functions, and even syntax.

Jinja's philosophy is that while application logic belongs in Python if
possible, it shouldn't make the template designer's job difficult by
restricting functionality too much.


Installation
------------

We recommend using the latest version of Python. Jinja supports Python
3.6 and newer. We also recommend using a `virtual environment`_ in order
to isolate your project dependencies from other projects and the system.

.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments

Install the most recent Jinja version using pip:

.. code-block:: text

    $ pip install Jinja2


Dependencies
~~~~~~~~~~~~

These will be installed automatically when installing Jinja.

-   `MarkupSafe`_ escapes untrusted input when rendering templates to
    avoid injection attacks.

.. _MarkupSafe: https://markupsafe.palletsprojects.com/


Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

These distributions will not be installed automatically.

-   `Babel`_ provides translation support in templates.

.. _Babel: http://babel.pocoo.org/
