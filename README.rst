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

The `Jinja2 tip`_ is installable via ``pip`` with ``pip install
https://github.com/pallets/jinja/zipball/master``.

.. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
.. _Django: http://www.djangoproject.com/
.. _Jinja2 webpage: http://jinja.pocoo.org/
.. _documentation: http://jinja.pocoo.org/docs/
.. _Jinja2 tip: http://jinja.pocoo.org/docs/intro/#as-a-python-egg-via-easy-install

Builds
------

+---------------------+------------------------------------------------------------------------------+
| ``master``          | .. image:: https://travis-ci.org/pallets/jinja.svg?branch=master             |
|                     |     :target: https://travis-ci.org/pallets/jinja                             |
+---------------------+------------------------------------------------------------------------------+
| ``2.9-maintenance`` | .. image:: https://travis-ci.org/pallets/jinja.svg?branch=2.9-maintenance    |
|                     |     :target: https://travis-ci.org/pallets/jinja                             |
+---------------------+------------------------------------------------------------------------------+
