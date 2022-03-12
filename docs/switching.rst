Switching From Other Template Engines
=====================================

This is a brief guide on some of the differences between Jinja syntax
and other template languages. See :doc:`/templates` for a comprehensive
guide to Jinja syntax and features.


Django
------

If you have previously worked with Django templates, you should find
Jinja very familiar. Many of the syntax elements look and work the same.
However, Jinja provides some more syntax elements, and some work a bit
differently.

This section covers the template changes. The API, including extension
support, is fundamentally different so it won't be covered here.

Django supports using Jinja as its template engine, see
https://docs.djangoproject.com/en/stable/topics/templates/#support-for-template-engines.


Method Calls
~~~~~~~~~~~~

In Django, methods are called implicitly, without parentheses.

.. code-block:: django

    {% for page in user.get_created_pages %}
        ...
    {% endfor %}

In Jinja, using parentheses is required for calls, like in Python. This
allows you to pass variables to the method, which is not possible
in Django. This syntax is also used for calling macros.

.. code-block:: jinja

    {% for page in user.get_created_pages() %}
        ...
    {% endfor %}


Filter Arguments
~~~~~~~~~~~~~~~~

In Django, one literal value can be passed to a filter after a colon.

.. code-block:: django

    {{ items|join:", " }}

In Jinja, filters can take any number of positional and keyword
arguments in parentheses, like function calls. Arguments can also be
variables instead of literal values.

.. code-block:: jinja

    {{ items|join(", ") }}


Tests
~~~~~

In addition to filters, Jinja also has "tests" used with the ``is``
operator. This operator is not the same as the Python operator.

.. code-block:: jinja

    {% if user.user_id is odd %}
        {{ user.username|e }} is odd
    {% else %}
        hmm. {{ user.username|e }} looks pretty normal
    {% endif %}

Loops
~~~~~

In Django, the special variable for the loop context is called
``forloop``, and the ``empty`` is used for no loop items.

.. code-block:: django

    {% for item in items %}
        {{ item }}
    {% empty %}
        No items!
    {% endfor %}

In Jinja, the special variable for the loop context is called ``loop``,
and the ``else`` block is used for no loop items.

.. code-block:: jinja

    {% for item in items %}
        {{ loop.index}}. {{ item }}
    {% else %}
        No items!
    {% endfor %}


Cycle
~~~~~

In Django, the ``{% cycle %}`` can be used in a for loop to alternate
between values per loop.

.. code-block:: django

    {% for user in users %}
        <li class="{% cycle 'odd' 'even' %}">{{ user }}</li>
    {% endfor %}

In Jinja, the ``loop`` context has a ``cycle`` method.

.. code-block:: jinja

    {% for user in users %}
        <li class="{{ loop.cycle('odd', 'even') }}">{{ user }}</li>
    {% endfor %}

A cycler can also be assigned to a variable and used outside or across
loops with the ``cycle()`` global function.


Mako
----

You can configure Jinja to look more like Mako:

.. code-block:: python

    env = Environment(
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="${",
        variable_end_string="}",
        comment_start_string="<%doc>",
        commend_end_string="</%doc>",
        line_statement_prefix="%",
        line_comment_prefix="##",
    )

With an environment configured like that, Jinja should be able to
interpret a small subset of Mako templates without any changes.

Jinja does not support embedded Python code, so you would have to move
that out of the template. You could either process the data with the
same code before rendering, or add a global function or filter to the
Jinja environment.

The syntax for defs (which are called macros in Jinja) and template
inheritance is different too.

The following Mako template:

.. code-block:: mako

    <%inherit file="layout.html" />
    <%def name="title()">Page Title</%def>
    <ul>
    % for item in list:
        <li>${item}</li>
    % endfor
    </ul>

Looks like this in Jinja with the above configuration:

.. code-block:: jinja

    <% extends "layout.html" %>
    <% block title %>Page Title<% endblock %>
    <% block body %>
    <ul>
    % for item in list:
        <li>${item}</li>
    % endfor
    </ul>
    <% endblock %>
