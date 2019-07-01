Jinja2
~~~~~~

Jinja2 is a template engine written in pure Python.  It provides a
`Django`_ inspired non-XML syntax but supports inline expressions and
an optional `sandboxed`_ environment.

Nutshell
--------

Here a small example of a Jinja template:

.. code-block:: jinja

    {% extends 'base.html' %}
    {% block title %}Memberlist{% endblock %}
    {% block content %}
      <ul>
      {% for user in users %}
        <li><a href="{{ user.url }}">{{ user.username }}</a></li>
      {% endfor %}
      </ul>
    {% endblock %}

Philosophy
----------

Application logic is for the controller, but don't make the template designer's
life difficult by restricting functionality too much.

For more information visit the new `Jinja2 webpage`_ and `documentation`_.
The source code can be found in Jinja2's `Github repository`_.

.. _sandboxed: https://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: https://www.djangoproject.com/
.. _Jinja2 webpage: http://jinja.pocoo.org/
.. _documentation: http://jinja.pocoo.org/2/documentation/
.. _Github repository: https://github.com/pallets/jinja/

Builds
------

+---------------------+------------------------------------------------------------------------------+
| ``master``          | .. image:: https://travis-ci.org/pallets/jinja.svg?branch=master             |
|                     |     :target: https://travis-ci.org/pallets/jinja                             |
+---------------------+------------------------------------------------------------------------------+
| ``2.9-maintenance`` | .. image:: https://travis-ci.org/pallets/jinja.svg?branch=2.9-maintenance    |
|                     |     :target: https://travis-ci.org/pallets/jinja                             |
+---------------------+------------------------------------------------------------------------------+
