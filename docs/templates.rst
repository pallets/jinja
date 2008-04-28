Template Designer Documentation
===============================

This document describes the syntax and semantics of the template engine and
will be most useful as reference to those creating Jinja templates.  As the
template engine is very flexible the configuration from the application might
be slightly different from here in terms of delimiters and behavior of
undefined values.


Synopsis
--------

A template is simply a text file.  It can generate any text-based format
(HTML, XML, CSV, LaTeX, etc.).  It doesn't have a specific extension,
``.html`` or ``.xml`` are just fine.

A template contains **variables** or **expressions**, which get replaced with
values when the template is evaluated, and tags, which control the logic of
the template.  The template syntax is heavily inspired by Django and Python.

Below is a minimal template that illustrates a few basics.  We will cover
the details later in that document:

.. sourcecode:: html+jinja

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
    <html lang="en">
    <head>
        <title>My Webpage</title>
    </head>
    <body>
        <ul id="navigation">
        {% for item in navigation %}
            <li><a href="{{ item.href }}">{{ item.caption }}</a></li>
        {% endfor %}
        </ul>

        <h1>My Webpage</h1>
        {{ a_variable }}
    </body>
    </html>

This covers the default settings.  The application developer might have
changed the syntax from ``{% foo %}`` to ``<% foo %>`` or something similar.

There are two kinds of delimiers. ``{% ... %}`` and ``{{ ... }}``.  The first
one is used to execute statements such as for-loops or assign values, the
latter prints the result of the expression to the template.


Variables
---------

The application passes variables to the templates you can mess around in the
template.  Variables may have attributes or elements on them you can access
too.  How a variable looks like, heavily depends on the application providing
those.

You can use a dot (``.``) to access attributes of a variable, alternative the
so-called "subscribe" syntax (``[]``) can be used.  The following lines do
the same:

.. sourcecode:: jinja

    {{ foo.bar }}
    {{ foo['bar'] }}

It's important to know that the curly braces are *not* part of the variable
but the print statement.  If you access variables inside tags don't put the
braces around.

If a variable or attribute does not exist you will get back an undefined
value.  What you can do with that kind of value depends on the application
configuration, the default behavior is that it evaluates to an empty string
if printed and that you can iterate over it, but every other operation fails.


Filters
-------

Variables can by modified by **filters**.  Filters are separated from the
variable by a pipe symbol (``|``) and may have optional arguments in
parentheses.  Multiple filters can be chained.  The output of one filter is
applied to the next.

``{{ name|striptags|title }}`` for example will remove all HTML Tags from the
`name` and title-cases it.  Filters that accept arguments have parentheses
around the arguments, like a function call.  This example will join a list
by spaces:  ``{{ list|join(', ') }}``.

The :ref:`builtin-filters` below describes all the builtin filters.


Tests
-----

Beside filters there are also so called "tests" available.  Tests can be used
to test a variable against a common expression.  To test a variable or
expression you add `is` plus the name of the test after the variable.  For
example to find out if a variable is defined you can do ``name is defined``
which will then return true or false depening on if `name` is defined.

Tests can accept arguments too.  If the test only takes one argument you can
leave out the parentheses to group them.  For example the following two
expressions do the same:

.. sourcecode:: jinja

    {% if loop.index is divisibleby 3 %}
    {% if loop.index is divisibleby(3) %}

The :ref:`builtin-tests` below descibes all the builtin tests.


Comments
--------

To comment-out part of a line in a template, use the comment syntax which is
by default set to ``{# ... #}``.  This is useful to comment out parts of the
template for debugging or to add information for other template designers or
yourself:

.. sourcecode:: jinja

    {# note: disabled template because we no longer user this
        {% for user in users %}
            ...
        {% endfor %}
    #}


Template Inheritance
--------------------

The most powerful part of Jinja is template inheritance. Template inheritance
allows you to build a base "skeleton" template that contains all the common
elements of your site and defines **blocks** that child templates can override.

Sounds complicated but is very basic. It's easiest to understand it by starting
with an example.


Base Template
~~~~~~~~~~~~~

This template, which we'll call ``base.html``, defines a simple HTML skeleton
document that you might use for a simple two-column page. It's the job of
"child" templates to fill the empty blocks with content:

.. sourcecode:: html+jinja

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
    <html lang="en">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        {% block head %}
        <link rel="stylesheet" href="style.css" />
        <title>{% block title %}{% endblock %} - My Webpage</title>
        {% endblock %}
    </head>
    <body>
        <div id="content">{% block content %}{% endblock %}</div>
        <div id="footer">
            {% block footer %}
            &copy; Copyright 2008 by <a href="http://domain.invalid/">you</a>.
            {% endblock %}
        </div>
    </body>

In this example, the ``{% block %}`` tags define four blocks that child templates
can fill in. All the `block` tag does is to tell the template engine that a
child template may override those portions of the template.

Child Template
~~~~~~~~~~~~~~

A child template might look like this:

.. sourcecode:: html+jinja

    {% extends "base.html" %}
    {% block title %}Index{% endblock %}
    {% block head %}
        {{ super() }}
        <style type="text/css">
            .important { color: #336699; }
        </style>
    {% endblock %}
    {% block content %}
        <h1>Index</h1>
        <p class="important">
          Welcome on my awsome homepage.
        </p>
    {% endblock %}

The ``{% extends %}`` tag is the key here. It tells the template engine that
this template "extends" another template.  When the template system evaluates
this template, first it locates the parent.  The extends tag should be the
first tag in the template.  Everything before it is printed out normally and
may cause confusion.

The filename of the template depends on the template loader.  For example the
:class:`FileSystemLoader` allows you to access other templates by giving the
filename.  You can access templates in subdirectories with an slash:

.. sourcecode:: jinja

    {% extends "layout/default.html" %}

But this behavior can depend on the application embedding Jinja.  Note that
since the child template doesn't define the ``footer`` block, the value from
the parent template is used instead.

You can't define multiple ``{% block %}`` tags with the same name in the
same template.  This limitation exists because a block tag works in "both"
directions.  That is, a block tag doesn't just provide a hole to fill - it
also defines the content that fills the hole in the *parent*.  If there
were two similarly-named ``{% block %}`` tags in a template, that template's
parent wouldn't know which one of the blocks' content to use.

If you want to print a block multiple times you can however use the special
`self` variable and call the block with that name:

.. sourcecode:: jinja

    <title>{% block title %}{% endblock %}</title>
    <h1>{{ self.title() }}</h1>
    {% block body %}{% endblock %}


Unlike Python Jinja does not support multiple inheritance.  So you can only have
one extends tag called per rendering.


Super Blocks
~~~~~~~~~~~~

It's possible to render the contents of the parent block by calling `super`.
This gives back the results of the parent block:

.. sourcecode:: jinja

    {% block sidebar %}
        <h3>Table Of Contents</h3>
        ...
        {{ super() }}
    {% endblock %}


HTML Escaping
-------------

When generating HTML from templates, there's always a risk that a variable will
include characters that affect the resulting HTML.  There are two approaches:
manually escaping each variable or automatically escaping everything by default.

Jinja supports both, but what is used depends on the application configuration.
The default configuaration is no automatic escaping for various reasons:

-   escaping everything except of safe values will also mean that Jinja is
    escaping variables known to not include HTML such as numbers which is
    a huge performance hit.

-   The information about the safety of a variable is very fragile.  It could
    happen that by coercing safe and unsafe values the return value is double
    escaped HTML.

Working with Manual Escaping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If manual escaping is enabled it's **your** responsibility to escape
variables if needed.  What to escape?  If you have a variable that *may*
include any of the following chars (``>``, ``<``, ``&``, or ``"``) you
**have to** escape it unless the variable contains well-formed and trusted
HTML.  Escaping works by piping the variable through the ``|e`` filter:
``{{ user.username|e }}``.

Working with Automatic Escaping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When automatic escaping is enabled everything is escaped by default except
for values explicitly marked as safe.  Those can either be marked by the
application or in the template by using the `|safe` filter.  The main
problem with this approach is that Python itself doesn't have the concept
of tainted values so the information if a value is safe or unsafe can get
lost.  If the information is lost escaping will take place which means that
you could end up with double escaped contents.

Double escaping is easy to avoid however, just relay on the tools Jinja2
provides and don't use builtin Python constructs such as the string modulo
operator.

Functions returning template data (macros, `super`, `self.BLOCKNAME`) return
safe markup always.

String literals in templates with automatic escaping are considered unsafe
too.  The reason for this is that the safe string is an extension to Python
and not every library will work properly with it.


List of Control Structures
--------------------------

A control structure refers to all those things that control the flow of a
program - conditionals (i.e. if/elif/else), for-loops, as well as things like
macros and blocks.  Control structures appear inside ``{% ... %}`` blocks
in the default syntax.

For Loops
~~~~~~~~~

Loop over each item in a sequece.  For example, to display a list of users
provided in a variable called `users`:

.. sourcecode:: html+jinja

    <h1>Members</h1>
    <ul>
    {% for user in users %}
      <li>{{ user.username|e }}</li>
    {% endfor %}
    </ul>

Inside of a for loop block you can access some special variables:

+-----------------------+---------------------------------------------------+
| `loop.index`          | The current iteration of the loop. (1 indexed)    |
+-----------------------+---------------------------------------------------+
| `loop.index0`         | The current iteration of the loop. (0 indexed)    |
+-----------------------+---------------------------------------------------+
| `loop.revindex`       | The number of iterations from the end of the loop |
|                       | (1 indexed)                                       |
+-----------------------+---------------------------------------------------+
| `loop.revindex0`      | The number of iterations from the end of the loop |
|                       | (0 indexed)                                       |
+-----------------------+---------------------------------------------------+
| `loop.first`          | True if first iteration.                          |
+-----------------------+---------------------------------------------------+
| `loop.last`           | True if last iteration.                           |
+-----------------------+---------------------------------------------------+
| `loop.length`         | The number of items in the sequence.              |
+-----------------------+---------------------------------------------------+
| `loop.cycle`          | A helper function to cycle between a list of      |
|                       | sequences.  See the explanation below.            |
+-----------------------+---------------------------------------------------+

Within a for-loop, it's psosible to cycle among a list of strings/variables
each time through the loop by using the special `loop.cycle` helper:

.. sourcecode:: html+jinja

    {% for row in rows %}
        <li class="{{ loop.cycle('odd', 'even') }}">{{ row }}</li>
    {% endfor %}

Unlike in Python it's not possible to `break` or `continue` in a loop.  You
can however filter the sequence during iteration which allows you to skip
items.  The following example skips all the users which are hidden:

.. sourcecode:: html+jinja

    {% for user in users if not user.hidden %}
        <li>{{ user.username|e }}</li>
    {% endfor %}

The advantage is that the special `loop` variable will count correctly thus
not counting the users not iterated over.

If no iteration took place because the sequence was empty or the filtering
removed all the items from the sequence you can render a replacement block
by using `else`:

.. sourcecode:: html+jinja

    <ul>
    {% for user in users %}
        <li>{{ user.username|e }}</li>
    {% else %}
        <li><em>no users found</em></li>
    {% endif %}
    </ul>
    

.. _builtin-filters:

List of Builtin Filters
-----------------------

.. jinjafilters::


.. _builtin-tests:

List of Builtin Tests
---------------------

.. jinjatests::
