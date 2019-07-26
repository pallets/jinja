.. rst-class:: hide-header

Jinja
=====

.. image:: _static/jinja-logo.png
    :align: center
    :target: https://palletsprojects.com/p/jinja/

Jinja is a modern and designer-friendly templating language for Python,
modelled after Django's templates.  It is fast, widely used and secure
with the optional sandboxed template execution environment:

.. sourcecode:: html+jinja

   <title>{% block title %}{% endblock %}</title>
   <ul>
   {% for user in users %}
     <li><a href="{{ user.url }}">{{ user.username }}</a></li>
   {% endfor %}
   </ul>

Features:

-   sandboxed execution
-   powerful automatic HTML escaping system for XSS prevention
-   template inheritance
-   compiles down to the optimal python code just in time
-   optional ahead-of-time template compilation
-   easy to debug.  Line numbers of exceptions directly point to
    the correct line in the template.
-   configurable syntax

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    intro
    api
    sandbox
    nativetypes
    templates
    extensions
    integration
    switching
    tricks
    faq
    changelog

* :ref:`genindex`
* :ref:`search`
