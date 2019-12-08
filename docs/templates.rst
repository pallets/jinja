Template Designer Documentation
===============================

.. highlight:: html+jinja

This document describes the syntax and semantics of the template engine and
will be most useful as reference to those creating Jinja templates.  As the
template engine is very flexible, the configuration from the application can
be slightly different from the code presented here in terms of delimiters and
behavior of undefined values.


Synopsis
--------

A Jinja template is simply a text file. Jinja can generate any text-based
format (HTML, XML, CSV, LaTeX, etc.).  A Jinja template doesn't need to have a
specific extension: ``.html``, ``.xml``, or any other extension is just fine.

A template contains **variables** and/or **expressions**, which get replaced
with values when a template is *rendered*; and **tags**, which control the
logic of the template.  The template syntax is heavily inspired by Django and
Python.

Below is a minimal template that illustrates a few basics using the default
Jinja configuration.  We will cover the details later in this document::

    <!DOCTYPE html>
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

        {# a comment #}
    </body>
    </html>

The following example shows the default configuration settings.  An application
developer can change the syntax configuration from ``{% foo %}`` to ``<% foo
%>``, or something similar.

There are a few kinds of delimiters. The default Jinja delimiters are
configured as follows:

* ``{% ... %}`` for :ref:`Statements <list-of-control-structures>`
* ``{{ ... }}`` for :ref:`Expressions` to print to the template output
* ``{# ... #}`` for :ref:`Comments` not included in the template output
* ``#  ... ##`` for :ref:`Line Statements <line-statements>`


Template File Extension
~~~~~~~~~~~~~~~~~~~~~~~

As stated above, any file can be loaded as a template, regardless of
file extension. Adding a ``.jinja`` extension, like ``user.html.jinja``
may make it easier for some IDEs or editor plugins, but is not required.
Autoescaping, introduced later, can be applied based on file extension,
so you'll need to take the extra suffix into account in that case.

Another good heuristic for identifying templates is that they are in a
``templates`` folder, regardless of extension. This is a common layout
for projects.


.. _variables:

Variables
---------

Template variables are defined by the context dictionary passed to the
template.

You can mess around with the variables in templates provided they are passed in
by the application.  Variables may have attributes or elements on them you can
access too.  What attributes a variable has depends heavily on the application
providing that variable.

You can use a dot (``.``) to access attributes of a variable in addition
to the standard Python ``__getitem__`` "subscript" syntax (``[]``).

The following lines do the same thing::

    {{ foo.bar }}
    {{ foo['bar'] }}

It's important to know that the outer double-curly braces are *not* part of the
variable, but the print statement.  If you access variables inside tags don't
put the braces around them.

If a variable or attribute does not exist, you will get back an undefined
value.  What you can do with that kind of value depends on the application
configuration: the default behavior is to evaluate to an empty string if
printed or iterated over, and to fail for every other operation.

.. _notes-on-subscriptions:

.. admonition:: Implementation

    For the sake of convenience, ``foo.bar`` in Jinja does the following
    things on the Python layer:

    -   check for an attribute called `bar` on `foo`
        (``getattr(foo, 'bar')``)
    -   if there is not, check for an item ``'bar'`` in `foo`
        (``foo.__getitem__('bar')``)
    -   if there is not, return an undefined object.

    ``foo['bar']`` works mostly the same with a small difference in sequence:

    -   check for an item ``'bar'`` in `foo`.
        (``foo.__getitem__('bar')``)
    -   if there is not, check for an attribute called `bar` on `foo`.
        (``getattr(foo, 'bar')``)
    -   if there is not, return an undefined object.

    This is important if an object has an item and attribute with the same
    name.  Additionally, the :func:`attr` filter only looks up attributes.

.. _filters:

Filters
-------

Variables can be modified by **filters**.  Filters are separated from the
variable by a pipe symbol (``|``) and may have optional arguments in
parentheses.  Multiple filters can be chained.  The output of one filter is
applied to the next.

For example, ``{{ name|striptags|title }}`` will remove all HTML Tags from
variable `name` and title-case the output (``title(striptags(name))``).

Filters that accept arguments have parentheses around the arguments, just like
a function call.  For example: ``{{ listx|join(', ') }}`` will join a list with
commas (``str.join(', ', listx)``).

The :ref:`builtin-filters` below describes all the builtin filters.

.. _tests:

Tests
-----

Beside filters, there are also so-called "tests" available.  Tests can be used
to test a variable against a common expression.  To test a variable or
expression, you add `is` plus the name of the test after the variable.  For
example, to find out if a variable is defined, you can do ``name is defined``,
which will then return true or false depending on whether `name` is defined
in the current template context.

Tests can accept arguments, too.  If the test only takes one argument, you can
leave out the parentheses.  For example, the following two
expressions do the same thing::

    {% if loop.index is divisibleby 3 %}
    {% if loop.index is divisibleby(3) %}

The :ref:`builtin-tests` below describes all the builtin tests.


.. _comments:

Comments
--------

To comment-out part of a line in a template, use the comment syntax which is
by default set to ``{# ... #}``.  This is useful to comment out parts of the
template for debugging or to add information for other template designers or
yourself::

    {# note: commented-out template because we no longer use this
        {% for user in users %}
            ...
        {% endfor %}
    #}


Whitespace Control
------------------

In the default configuration:

* a single trailing newline is stripped if present
* other whitespace (spaces, tabs, newlines etc.) is returned unchanged

If an application configures Jinja to `trim_blocks`, the first newline after a
template tag is removed automatically (like in PHP). The `lstrip_blocks`
option can also be set to strip tabs and spaces from the beginning of a
line to the start of a block. (Nothing will be stripped if there are
other characters before the start of the block.)

With both `trim_blocks` and `lstrip_blocks` enabled, you can put block tags
on their own lines, and the entire block line will be removed when
rendered, preserving the whitespace of the contents.  For example,
without the `trim_blocks` and `lstrip_blocks` options, this template::

    <div>
        {% if True %}
            yay
        {% endif %}
    </div>

gets rendered with blank lines inside the div::

    <div>

            yay

    </div>

But with both `trim_blocks` and `lstrip_blocks` enabled, the template block
lines are removed and other whitespace is preserved::

    <div>
            yay
    </div>

You can manually disable the `lstrip_blocks` behavior by putting a
plus sign (``+``) at the start of a block::

    <div>
            {%+ if something %}yay{% endif %}
    </div>

You can also strip whitespace in templates by hand.  If you add a minus
sign (``-``) to the start or end of a block (e.g. a :ref:`for-loop` tag), a
comment, or a variable expression, the whitespaces before or after
that block will be removed::

    {% for item in seq -%}
        {{ item }}
    {%- endfor %}

This will yield all elements without whitespace between them.  If `seq` was
a list of numbers from ``1`` to ``9``, the output would be ``123456789``.

If :ref:`line-statements` are enabled, they strip leading whitespace
automatically up to the beginning of the line.

By default, Jinja also removes trailing newlines.  To keep single
trailing newlines, configure Jinja to `keep_trailing_newline`.

.. admonition:: Note

    You must not add whitespace between the tag and the minus sign.

    **valid**::

        {%- if foo -%}...{% endif %}

    **invalid**::

        {% - if foo - %}...{% endif %}


Escaping
--------

It is sometimes desirable -- even necessary -- to have Jinja ignore parts
it would otherwise handle as variables or blocks.  For example, if, with
the default syntax, you want to use ``{{`` as a raw string in a template and
not start a variable, you have to use a trick.

The easiest way to output a literal variable delimiter (``{{``) is by using a
variable expression::

    {{ '{{' }}

For bigger sections, it makes sense to mark a block `raw`.  For example, to
include example Jinja syntax in a template, you can use this snippet::

    {% raw %}
        <ul>
        {% for item in seq %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    {% endraw %}

.. admonition:: Note

    Minus sign at the end of ``{% raw -%}`` tag cleans all the spaces and newlines
    preceding the first character of your raw data.


.. _line-statements:

Line Statements
---------------

If line statements are enabled by the application, it's possible to mark a
line as a statement.  For example, if the line statement prefix is configured
to ``#``, the following two examples are equivalent::

    <ul>
    # for item in seq
        <li>{{ item }}</li>
    # endfor
    </ul>

    <ul>
    {% for item in seq %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>

The line statement prefix can appear anywhere on the line as long as no text
precedes it.  For better readability, statements that start a block (such as
`for`, `if`, `elif` etc.) may end with a colon::

    # for item in seq:
        ...
    # endfor


.. admonition:: Note

    Line statements can span multiple lines if there are open parentheses,
    braces or brackets::

        <ul>
        # for href, caption in [('index.html', 'Index'),
                                ('about.html', 'About')]:
            <li><a href="{{ href }}">{{ caption }}</a></li>
        # endfor
        </ul>

Since Jinja 2.2, line-based comments are available as well.  For example, if
the line-comment prefix is configured to be ``##``, everything from ``##`` to
the end of the line is ignored (excluding the newline sign)::

    # for item in seq:
        <li>{{ item }}</li>     ## this comment is ignored
    # endfor


.. _template-inheritance:

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
"child" templates to fill the empty blocks with content::

    <!DOCTYPE html>
    <html lang="en">
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
    </html>

In this example, the ``{% block %}`` tags define four blocks that child templates
can fill in. All the `block` tag does is tell the template engine that a
child template may override those placeholders in the template.

``block`` tags can be inside other blocks such as ``if``, but they will
always be executed regardless of if the ``if`` block is actually
rendered.

Child Template
~~~~~~~~~~~~~~

A child template might look like this::

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
          Welcome to my awesome homepage.
        </p>
    {% endblock %}

The ``{% extends %}`` tag is the key here. It tells the template engine that
this template "extends" another template.  When the template system evaluates
this template, it first locates the parent.  The extends tag should be the
first tag in the template.  Everything before it is printed out normally and
may cause confusion.  For details about this behavior and how to take
advantage of it, see :ref:`null-master-fallback`. Also a block will always be
filled in regardless of whether the surrounding condition is evaluated to be true
or false.

The filename of the template depends on the template loader.  For example, the
:class:`FileSystemLoader` allows you to access other templates by giving the
filename.  You can access templates in subdirectories with a slash::

    {% extends "layout/default.html" %}

But this behavior can depend on the application embedding Jinja.  Note that
since the child template doesn't define the ``footer`` block, the value from
the parent template is used instead.

You can't define multiple ``{% block %}`` tags with the same name in the
same template.  This limitation exists because a block tag works in "both"
directions.  That is, a block tag doesn't just provide a placeholder to fill
- it also defines the content that fills the placeholder in the *parent*.
If there were two similarly-named ``{% block %}`` tags in a template,
that template's parent wouldn't know which one of the blocks' content to use.

If you want to print a block multiple times, you can, however, use the special
`self` variable and call the block with that name::

    <title>{% block title %}{% endblock %}</title>
    <h1>{{ self.title() }}</h1>
    {% block body %}{% endblock %}


Super Blocks
~~~~~~~~~~~~

It's possible to render the contents of the parent block by calling ``super()``.
This gives back the results of the parent block::

    {% block sidebar %}
        <h3>Table Of Contents</h3>
        ...
        {{ super() }}
    {% endblock %}


Nesting extends
~~~~~~~~~~~~~~~

In the case of multiple levels of ``{% extends %}``,
``super`` references may be chained (as in ``super.super()``)
to skip levels in the inheritance tree.

For example::

    # parent.tmpl
    body: {% block body %}Hi from parent.{% endblock %}

    # child.tmpl
    {% extends "parent.tmpl" %}
    {% block body %}Hi from child. {{ super() }}{% endblock %}

    # grandchild1.tmpl
    {% extends "child.tmpl" %}
    {% block body %}Hi from grandchild1.{% endblock %}

    # grandchild2.tmpl
    {% extends "child.tmpl" %}
    {% block body %}Hi from grandchild2. {{ super.super() }} {% endblock %}


Rendering ``child.tmpl`` will give
``body: Hi from child. Hi from parent.``

Rendering ``grandchild1.tmpl`` will give
``body: Hi from grandchild1.``

Rendering ``grandchild2.tmpl`` will give
``body: Hi from grandchild2. Hi from parent.``


Named Block End-Tags
~~~~~~~~~~~~~~~~~~~~

Jinja allows you to put the name of the block after the end tag for better
readability::

    {% block sidebar %}
        {% block inner_sidebar %}
            ...
        {% endblock inner_sidebar %}
    {% endblock sidebar %}

However, the name after the `endblock` word must match the block name.


Block Nesting and Scope
~~~~~~~~~~~~~~~~~~~~~~~

Blocks can be nested for more complex layouts.  However, per default blocks
may not access variables from outer scopes::

    {% for item in seq %}
        <li>{% block loop_item %}{{ item }}{% endblock %}</li>
    {% endfor %}

This example would output empty ``<li>`` items because `item` is unavailable
inside the block.  The reason for this is that if the block is replaced by
a child template, a variable would appear that was not defined in the block or
passed to the context.

Starting with Jinja 2.2, you can explicitly specify that variables are
available in a block by setting the block to "scoped" by adding the `scoped`
modifier to a block declaration::

    {% for item in seq %}
        <li>{% block loop_item scoped %}{{ item }}{% endblock %}</li>
    {% endfor %}

When overriding a block, the `scoped` modifier does not have to be provided.


Template Objects
~~~~~~~~~~~~~~~~

.. versionchanged:: 2.4

If a template object was passed in the template context, you can
extend from that object as well.  Assuming the calling code passes
a layout template as `layout_template` to the environment, this
code works::

    {% extends layout_template %}

Previously, the `layout_template` variable had to be a string with
the layout template's filename for this to work.


HTML Escaping
-------------

When generating HTML from templates, there's always a risk that a variable will
include characters that affect the resulting HTML. There are two approaches:

a. manually escaping each variable; or
b. automatically escaping everything by default.

Jinja supports both. What is used depends on the application configuration.
The default configuration is no automatic escaping; for various reasons:

-   Escaping everything except for safe values will also mean that Jinja is
    escaping variables known to not include HTML (e.g. numbers, booleans)
    which can be a huge performance hit.

-   The information about the safety of a variable is very fragile.  It could
    happen that by coercing safe and unsafe values, the return value is
    double-escaped HTML.

Working with Manual Escaping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If manual escaping is enabled, it's **your** responsibility to escape
variables if needed.  What to escape?  If you have a variable that *may*
include any of the following chars (``>``, ``<``, ``&``, or ``"``) you
**SHOULD** escape it unless the variable contains well-formed and trusted
HTML.  Escaping works by piping the variable through the ``|e`` filter::

    {{ user.username|e }}

Working with Automatic Escaping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When automatic escaping is enabled, everything is escaped by default except
for values explicitly marked as safe.  Variables and expressions
can be marked as safe either in:

a.  The context dictionary by the application with
    :class:`markupsafe.Markup`
b.  The template, with the ``|safe`` filter.

If a string that you marked safe is passed through other Python code
that doesn't understand that mark, it may get lost. Be aware of when
your data is marked safe and how it is processed before arriving at the
template.

If a value has been escaped but is not marked safe, auto-escaping will
still take place and result in double-escaped characters. If you know
you have data that is already safe but not marked, be sure to wrap it in
``Markup`` or use the ``|safe`` filter.

Jinja functions (macros, `super`, `self.BLOCKNAME`) always return template
data that is marked as safe.

String literals in templates with automatic escaping are considered unsafe
because native Python strings (``str``, ``unicode``, ``basestring``) are not
`MarkupSafe.Markup` strings with an ``__html__`` attribute.

.. _list-of-control-structures:

List of Control Structures
--------------------------

A control structure refers to all those things that control the flow of a
program - conditionals (i.e. if/elif/else), for-loops, as well as things like
macros and blocks.  With the default syntax, control structures appear inside
``{% ... %}`` blocks.

.. _for-loop:

For
~~~

Loop over each item in a sequence.  For example, to display a list of users
provided in a variable called `users`::

    <h1>Members</h1>
    <ul>
    {% for user in users %}
      <li>{{ user.username|e }}</li>
    {% endfor %}
    </ul>

As variables in templates retain their object properties, it is possible to
iterate over containers like `dict`::

    <dl>
    {% for key, value in my_dict.items() %}
        <dt>{{ key|e }}</dt>
        <dd>{{ value|e }}</dd>
    {% endfor %}
    </dl>

Note, however, that **Python dicts are not ordered**; so you might want to
either pass a sorted ``list`` of ``tuple`` s -- or a
``collections.OrderedDict`` -- to the template, or use the `dictsort` filter.

Inside of a for-loop block, you can access some special variables:

+-----------------------+---------------------------------------------------+
| Variable              | Description                                       |
+=======================+===================================================+
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
| `loop.depth`          | Indicates how deep in a recursive loop            |
|                       | the rendering currently is.  Starts at level 1    |
+-----------------------+---------------------------------------------------+
| `loop.depth0`         | Indicates how deep in a recursive loop            |
|                       | the rendering currently is.  Starts at level 0    |
+-----------------------+---------------------------------------------------+
| `loop.previtem`       | The item from the previous iteration of the loop. |
|                       | Undefined during the first iteration.             |
+-----------------------+---------------------------------------------------+
| `loop.nextitem`       | The item from the following iteration of the loop.|
|                       | Undefined during the last iteration.              |
+-----------------------+---------------------------------------------------+
| `loop.changed(*val)`  | True if previously called with a different value  |
|                       | (or not called at all).                           |
+-----------------------+---------------------------------------------------+

Within a for-loop, it's possible to cycle among a list of strings/variables
each time through the loop by using the special `loop.cycle` helper::

    {% for row in rows %}
        <li class="{{ loop.cycle('odd', 'even') }}">{{ row }}</li>
    {% endfor %}

Since Jinja 2.1, an extra `cycle` helper exists that allows loop-unbound
cycling.  For more information, have a look at the :ref:`builtin-globals`.

.. _loop-filtering:

Unlike in Python, it's not possible to `break` or `continue` in a loop.  You
can, however, filter the sequence during iteration, which allows you to skip
items.  The following example skips all the users which are hidden::

    {% for user in users if not user.hidden %}
        <li>{{ user.username|e }}</li>
    {% endfor %}

The advantage is that the special `loop` variable will count correctly; thus
not counting the users not iterated over.

If no iteration took place because the sequence was empty or the filtering
removed all the items from the sequence, you can render a default block
by using `else`::

    <ul>
    {% for user in users %}
        <li>{{ user.username|e }}</li>
    {% else %}
        <li><em>no users found</em></li>
    {% endfor %}
    </ul>

Note that, in Python, `else` blocks are executed whenever the corresponding
loop **did not** `break`.  Since Jinja loops cannot `break` anyway,
a slightly different behavior of the `else` keyword was chosen.

It is also possible to use loops recursively.  This is useful if you are
dealing with recursive data such as sitemaps or RDFa.
To use loops recursively, you basically have to add the `recursive` modifier
to the loop definition and call the `loop` variable with the new iterable
where you want to recurse.

The following example implements a sitemap with recursive loops::

    <ul class="sitemap">
    {%- for item in sitemap recursive %}
        <li><a href="{{ item.href|e }}">{{ item.title }}</a>
        {%- if item.children -%}
            <ul class="submenu">{{ loop(item.children) }}</ul>
        {%- endif %}</li>
    {%- endfor %}
    </ul>

The `loop` variable always refers to the closest (innermost) loop. If we
have more than one level of loops, we can rebind the variable `loop` by
writing `{% set outer_loop = loop %}` after the loop that we want to
use recursively. Then, we can call it using `{{ outer_loop(...) }}`

Please note that assignments in loops will be cleared at the end of the
iteration and cannot outlive the loop scope.  Older versions of Jinja had
a bug where in some circumstances it appeared that assignments would work.
This is not supported.  See :ref:`assignments` for more information about
how to deal with this.

If all you want to do is check whether some value has changed since the
last iteration or will change in the next iteration, you can use `previtem`
and `nextitem`::

    {% for value in values %}
        {% if loop.previtem is defined and value > loop.previtem %}
            The value just increased!
        {% endif %}
        {{ value }}
        {% if loop.nextitem is defined and loop.nextitem > value %}
            The value will increase even more!
        {% endif %}
    {% endfor %}

If you only care whether the value changed at all, using `changed` is even
easier::

    {% for entry in entries %}
        {% if loop.changed(entry.category) %}
            <h2>{{ entry.category }}</h2>
        {% endif %}
        <p>{{ entry.message }}</p>
    {% endfor %}

.. _if:

If
~~

The `if` statement in Jinja is comparable with the Python if statement.
In the simplest form, you can use it to test if a variable is defined, not
empty and not false::

    {% if users %}
    <ul>
    {% for user in users %}
        <li>{{ user.username|e }}</li>
    {% endfor %}
    </ul>
    {% endif %}

For multiple branches, `elif` and `else` can be used like in Python.  You can
use more complex :ref:`expressions` there, too::

    {% if kenny.sick %}
        Kenny is sick.
    {% elif kenny.dead %}
        You killed Kenny!  You bastard!!!
    {% else %}
        Kenny looks okay --- so far
    {% endif %}

If can also be used as an :ref:`inline expression <if-expression>` and for
:ref:`loop filtering <loop-filtering>`.

.. _macros:

Macros
~~~~~~

Macros are comparable with functions in regular programming languages.  They
are useful to put often used idioms into reusable functions to not repeat
yourself ("DRY").

Here's a small example of a macro that renders a form element::

    {% macro input(name, value='', type='text', size=20) -%}
        <input type="{{ type }}" name="{{ name }}" value="{{
            value|e }}" size="{{ size }}">
    {%- endmacro %}

The macro can then be called like a function in the namespace::

    <p>{{ input('username') }}</p>
    <p>{{ input('password', type='password') }}</p>

If the macro was defined in a different template, you have to
:ref:`import <import>` it first.

Inside macros, you have access to three special variables:

`varargs`
    If more positional arguments are passed to the macro than accepted by the
    macro, they end up in the special `varargs` variable as a list of values.

`kwargs`
    Like `varargs` but for keyword arguments.  All unconsumed keyword
    arguments are stored in this special variable.

`caller`
    If the macro was called from a :ref:`call<call>` tag, the caller is stored
    in this variable as a callable macro.

Macros also expose some of their internal details.  The following attributes
are available on a macro object:

`name`
    The name of the macro.  ``{{ input.name }}`` will print ``input``.

`arguments`
    A tuple of the names of arguments the macro accepts.

`defaults`
    A tuple of default values.

`catch_kwargs`
    This is `true` if the macro accepts extra keyword arguments (i.e.: accesses
    the special `kwargs` variable).

`catch_varargs`
    This is `true` if the macro accepts extra positional arguments (i.e.:
    accesses the special `varargs` variable).

`caller`
    This is `true` if the macro accesses the special `caller` variable and may
    be called from a :ref:`call<call>` tag.

If a macro name starts with an underscore, it's not exported and can't
be imported.


.. _call:

Call
~~~~

In some cases it can be useful to pass a macro to another macro.  For this
purpose, you can use the special `call` block.  The following example shows
a macro that takes advantage of the call functionality and how it can be
used::

    {% macro render_dialog(title, class='dialog') -%}
        <div class="{{ class }}">
            <h2>{{ title }}</h2>
            <div class="contents">
                {{ caller() }}
            </div>
        </div>
    {%- endmacro %}

    {% call render_dialog('Hello World') %}
        This is a simple dialog rendered by using a macro and
        a call block.
    {% endcall %}

It's also possible to pass arguments back to the call block.  This makes it
useful as a replacement for loops.  Generally speaking, a call block works
exactly like a macro without a name.

Here's an example of how a call block can be used with arguments::

    {% macro dump_users(users) -%}
        <ul>
        {%- for user in users %}
            <li><p>{{ user.username|e }}</p>{{ caller(user) }}</li>
        {%- endfor %}
        </ul>
    {%- endmacro %}

    {% call(user) dump_users(list_of_user) %}
        <dl>
            <dl>Realname</dl>
            <dd>{{ user.realname|e }}</dd>
            <dl>Description</dl>
            <dd>{{ user.description }}</dd>
        </dl>
    {% endcall %}


Filters
~~~~~~~

Filter sections allow you to apply regular Jinja filters on a block of
template data.  Just wrap the code in the special `filter` section::

    {% filter upper %}
        This text becomes uppercase
    {% endfilter %}


.. _assignments:

Assignments
~~~~~~~~~~~

Inside code blocks, you can also assign values to variables.  Assignments at
top level (outside of blocks, macros or loops) are exported from the template
like top level macros and can be imported by other templates.

Assignments use the `set` tag and can have multiple targets::

    {% set navigation = [('index.html', 'Index'), ('about.html', 'About')] %}
    {% set key, value = call_something() %}

.. admonition:: Scoping Behavior

    Please keep in mind that it is not possible to set variables inside a
    block and have them show up outside of it.  This also applies to
    loops.  The only exception to that rule are if statements which do not
    introduce a scope.  As a result the following template is not going
    to do what you might expect::

        {% set iterated = false %}
        {% for item in seq %}
            {{ item }}
            {% set iterated = true %}
        {% endfor %}
        {% if not iterated %} did not iterate {% endif %}

    It is not possible with Jinja syntax to do this.  Instead use
    alternative constructs like the loop else block or the special `loop`
    variable::

        {% for item in seq %}
            {{ item }}
        {% else %}
            did not iterate
        {% endfor %}

    As of version 2.10 more complex use cases can be handled using namespace
    objects which allow propagating of changes across scopes::

        {% set ns = namespace(found=false) %}
        {% for item in items %}
            {% if item.check_something() %}
                {% set ns.found = true %}
            {% endif %}
            * {{ item.title }}
        {% endfor %}
        Found item having something: {{ ns.found }}

    Note that the ``obj.attr`` notation in the `set` tag is only allowed for
    namespace objects; attempting to assign an attribute on any other object
    will raise an exception.

    .. versionadded:: 2.10 Added support for namespace objects


Block Assignments
~~~~~~~~~~~~~~~~~

.. versionadded:: 2.8

Starting with Jinja 2.8, it's possible to also use block assignments to
capture the contents of a block into a variable name.  This can be useful
in some situations as an alternative for macros.  In that case, instead of
using an equals sign and a value, you just write the variable name and then
everything until ``{% endset %}`` is captured.

Example::

    {% set navigation %}
        <li><a href="/">Index</a>
        <li><a href="/downloads">Downloads</a>
    {% endset %}

The `navigation` variable then contains the navigation HTML source.

.. versionchanged:: 2.10

Starting with Jinja 2.10, the block assignment supports filters.

Example::

    {% set reply | wordwrap %}
        You wrote:
        {{ message }}
    {% endset %}


.. _extends:

Extends
~~~~~~~

The `extends` tag can be used to extend one template from another.  You can
have multiple `extends` tags in a file, but only one of them may be executed at
a time.

See the section about :ref:`template-inheritance` above.


.. _blocks:

Blocks
~~~~~~

Blocks are used for inheritance and act as both placeholders and replacements
at the same time.  They are documented in detail in the
:ref:`template-inheritance` section.


Include
~~~~~~~

The `include` tag is useful to include a template and return the
rendered contents of that file into the current namespace::

    {% include 'header.html' %}
        Body
    {% include 'footer.html' %}

Included templates have access to the variables of the active context by
default.  For more details about context behavior of imports and includes,
see :ref:`import-visibility`.

From Jinja 2.2 onwards, you can mark an include with ``ignore missing``; in
which case Jinja will ignore the statement if the template to be included
does not exist.  When combined with ``with`` or ``without context``, it must
be placed *before* the context visibility statement.  Here are some valid
examples::

    {% include "sidebar.html" ignore missing %}
    {% include "sidebar.html" ignore missing with context %}
    {% include "sidebar.html" ignore missing without context %}

.. versionadded:: 2.2

You can also provide a list of templates that are checked for existence
before inclusion.  The first template that exists will be included.  If
`ignore missing` is given, it will fall back to rendering nothing if
none of the templates exist, otherwise it will raise an exception.

Example::

    {% include ['page_detailed.html', 'page.html'] %}
    {% include ['special_sidebar.html', 'sidebar.html'] ignore missing %}

.. versionchanged:: 2.4
   If a template object was passed to the template context, you can
   include that object using `include`.

.. _import:

Import
~~~~~~

Jinja supports putting often used code into macros.  These macros can go into
different templates and get imported from there.  This works similarly to the
import statements in Python.  It's important to know that imports are cached
and imported templates don't have access to the current template variables,
just the globals by default.  For more details about context behavior of
imports and includes, see :ref:`import-visibility`.

There are two ways to import templates.  You can import a complete template
into a variable or request specific macros / exported variables from it.

Imagine we have a helper module that renders forms (called `forms.html`)::

    {% macro input(name, value='', type='text') -%}
        <input type="{{ type }}" value="{{ value|e }}" name="{{ name }}">
    {%- endmacro %}

    {%- macro textarea(name, value='', rows=10, cols=40) -%}
        <textarea name="{{ name }}" rows="{{ rows }}" cols="{{ cols
            }}">{{ value|e }}</textarea>
    {%- endmacro %}

The easiest and most flexible way to access a template's variables
and macros is to import the whole template module into a variable.
That way, you can access the attributes::

    {% import 'forms.html' as forms %}
    <dl>
        <dt>Username</dt>
        <dd>{{ forms.input('username') }}</dd>
        <dt>Password</dt>
        <dd>{{ forms.input('password', type='password') }}</dd>
    </dl>
    <p>{{ forms.textarea('comment') }}</p>


Alternatively, you can import specific names from a template into the current
namespace::

    {% from 'forms.html' import input as input_field, textarea %}
    <dl>
        <dt>Username</dt>
        <dd>{{ input_field('username') }}</dd>
        <dt>Password</dt>
        <dd>{{ input_field('password', type='password') }}</dd>
    </dl>
    <p>{{ textarea('comment') }}</p>

Macros and variables starting with one or more underscores are private and
cannot be imported.

.. versionchanged:: 2.4
   If a template object was passed to the template context, you can
   import from that object.


.. _import-visibility:

Import Context Behavior
-----------------------

By default, included templates are passed the current context and imported
templates are not.  The reason for this is that imports, unlike includes,
are cached; as imports are often used just as a module that holds macros.

This behavior can be changed explicitly: by adding `with context`
or `without context` to the import/include directive, the current context
can be passed to the template and caching is disabled automatically.

Here are two examples::

    {% from 'forms.html' import input with context %}
    {% include 'header.html' without context %}

.. admonition:: Note

    In Jinja 2.0, the context that was passed to the included template
    did not include variables defined in the template.  As a matter of
    fact, this did not work::

        {% for box in boxes %}
            {% include "render_box.html" %}
        {% endfor %}

    The included template ``render_box.html`` is *not* able to access
    `box` in Jinja 2.0. As of Jinja 2.1, ``render_box.html`` *is* able
    to do so.


.. _expressions:

Expressions
-----------

Jinja allows basic expressions everywhere.  These work very similarly to
regular Python; even if you're not working with Python
you should feel comfortable with it.

Literals
~~~~~~~~

The simplest form of expressions are literals.  Literals are representations
for Python objects such as strings and numbers.  The following literals exist:

``"Hello World"``
    Everything between two double or single quotes is a string.  They are
    useful whenever you need a string in the template (e.g. as
    arguments to function calls and filters, or just to extend or include a
    template).

``42`` / ``123_456``
    Integers are whole numbers without a decimal part. The '_' character
    can be used to separate groups for legibility.

``42.23`` / ``42.1e2`` / ``123_456.789``
    Floating point numbers can be written using a '.' as a decimal mark.
    They can also be written in scientific notation with an upper or
    lower case 'e' to indicate the exponent part. The '_' character can
    be used to separate groups for legibility, but cannot be used in the
    exponent part.

``['list', 'of', 'objects']``
    Everything between two brackets is a list.  Lists are useful for storing
    sequential data to be iterated over.  For example, you can easily
    create a list of links using lists and tuples for (and with) a for loop::

        <ul>
        {% for href, caption in [('index.html', 'Index'), ('about.html', 'About'),
                                 ('downloads.html', 'Downloads')] %}
            <li><a href="{{ href }}">{{ caption }}</a></li>
        {% endfor %}
        </ul>

``('tuple', 'of', 'values')``
    Tuples are like lists that cannot be modified ("immutable").  If a tuple
    only has one item, it must be followed by a comma (``('1-tuple',)``).
    Tuples are usually used to represent items of two or more elements.
    See the list example above for more details.

``{'dict': 'of', 'key': 'and', 'value': 'pairs'}``
    A dict in Python is a structure that combines keys and values.  Keys must
    be unique and always have exactly one value.  Dicts are rarely used in
    templates; they are useful in some rare cases such as the :func:`xmlattr`
    filter.

``true`` / ``false``
    ``true`` is always true and ``false`` is always false.

.. admonition:: Note

    The special constants `true`, `false`, and `none` are indeed lowercase.
    Because that caused confusion in the past, (`True` used to expand
    to an undefined variable that was considered false),
    all three can now also be written in title case
    (`True`, `False`, and `None`).
    However, for consistency, (all Jinja identifiers are lowercase)
    you should use the lowercase versions.

Math
~~~~

Jinja allows you to calculate with values.  This is rarely useful in templates
but exists for completeness' sake.  The following operators are supported:

``+``
    Adds two objects together. Usually the objects are numbers, but if both are
    strings or lists, you can concatenate them this way.  This, however, is not
    the preferred way to concatenate strings!  For string concatenation, have
    a look-see at the ``~`` operator.  ``{{ 1 + 1 }}`` is ``2``.

``-``
    Subtract the second number from the first one.  ``{{ 3 - 2 }}`` is ``1``.

``/``
    Divide two numbers.  The return value will be a floating point number.
    ``{{ 1 / 2 }}`` is ``{{ 0.5 }}``.

``//``
    Divide two numbers and return the truncated integer result.
    ``{{ 20 // 7 }}`` is ``2``.

``%``
    Calculate the remainder of an integer division.  ``{{ 11 % 7 }}`` is ``4``.

``*``
    Multiply the left operand with the right one.  ``{{ 2 * 2 }}`` would
    return ``4``.  This can also be used to repeat a string multiple times.
    ``{{ '=' * 80 }}`` would print a bar of 80 equal signs.

``**``
    Raise the left operand to the power of the right operand.  ``{{ 2**3 }}``
    would return ``8``.

Comparisons
~~~~~~~~~~~

``==``
    Compares two objects for equality.

``!=``
    Compares two objects for inequality.

``>``
    ``true`` if the left hand side is greater than the right hand side.

``>=``
    ``true`` if the left hand side is greater or equal to the right hand side.

``<``
    ``true`` if the left hand side is lower than the right hand side.

``<=``
    ``true`` if the left hand side is lower or equal to the right hand side.

Logic
~~~~~

For ``if`` statements, ``for`` filtering, and ``if`` expressions, it can be useful to
combine multiple expressions:

``and``
    Return true if the left and the right operand are true.

``or``
    Return true if the left or the right operand are true.

``not``
    negate a statement (see below).

``(expr)``
    Parentheses group an expression.

.. admonition:: Note

    The ``is`` and ``in`` operators support negation using an infix notation,
    too: ``foo is not bar`` and ``foo not in bar`` instead of ``not foo is bar``
    and ``not foo in bar``.  All other expressions require a prefix notation:
    ``not (foo and bar).``


Other Operators
~~~~~~~~~~~~~~~

The following operators are very useful but don't fit into any of the other
two categories:

``in``
    Perform a sequence / mapping containment test.  Returns true if the left
    operand is contained in the right.  ``{{ 1 in [1, 2, 3] }}`` would, for
    example, return true.

``is``
    Performs a :ref:`test <tests>`.

``|``
    Applies a :ref:`filter <filters>`.

``~``
    Converts all operands into strings and concatenates them.

    ``{{ "Hello " ~ name ~ "!" }}`` would return (assuming `name` is set
    to ``'John'``) ``Hello John!``.

``()``
    Call a callable: ``{{ post.render() }}``.  Inside of the parentheses you
    can use positional arguments and keyword arguments like in Python:

    ``{{ post.render(user, full=true) }}``.

``.`` / ``[]``
    Get an attribute of an object.  (See :ref:`variables`)


.. _if-expression:

If Expression
~~~~~~~~~~~~~

It is also possible to use inline `if` expressions.  These are useful in some
situations.  For example, you can use this to extend from one template if a
variable is defined, otherwise from the default layout template::

    {% extends layout_template if layout_template is defined else 'master.html' %}

The general syntax is ``<do something> if <something is true> else <do
something else>``.

The `else` part is optional.  If not provided, the else block implicitly
evaluates into an :class:`Undefined` object (regardless of what ``undefined``
in the environment is set to):

.. sourcecode:: jinja

    {{ "[{}]".format(page.title) if page.title }}


.. _python-methods:

Python Methods
~~~~~~~~~~~~~~

You can also use any of the methods of defined on a variable's type.
The value returned from the method invocation is used as the value of the expression.
Here is an example that uses methods defined on strings (where ``page.title`` is a string):

.. code-block:: text

    {{ page.title.capitalize() }}

This works for methods on user-defined types. For example, if variable
``f`` of type ``Foo`` has a method ``bar`` defined on it, you can do the
following:

.. code-block:: text

    {{ f.bar(value) }}

Operator methods also work as expected. For example, ``%`` implements
printf-style for strings:

.. code-block:: text

    {{ "Hello, %s!" % name }}

Although you should prefer the ``.format`` method for that case (which
is a bit contrived in the context of rendering a template):

.. code-block:: text

    {{ "Hello, {}!".format(name) }}


.. _builtin-filters:

List of Builtin Filters
-----------------------

.. jinja:filters:: jinja2.defaults.DEFAULT_FILTERS


.. _builtin-tests:

List of Builtin Tests
---------------------

.. jinja:tests:: jinja2.defaults.DEFAULT_TESTS


.. _builtin-globals:

List of Global Functions
------------------------

The following functions are available in the global scope by default:

.. function:: range([start,] stop[, step])

    Return a list containing an arithmetic progression of integers.
    ``range(i, j)`` returns ``[i, i+1, i+2, ..., j-1]``;
    start (!) defaults to ``0``.
    When step is given, it specifies the increment (or decrement).
    For example, ``range(4)`` and ``range(0, 4, 1)`` return ``[0, 1, 2, 3]``.
    The end point is omitted!
    These are exactly the valid indices for a list of 4 elements.

    This is useful to repeat a template block multiple times, e.g.
    to fill a list.  Imagine you have 7 users in the list but you want to
    render three empty items to enforce a height with CSS::

        <ul>
        {% for user in users %}
            <li>{{ user.username }}</li>
        {% endfor %}
        {% for number in range(10 - users|count) %}
            <li class="empty"><span>...</span></li>
        {% endfor %}
        </ul>

.. function:: lipsum(n=5, html=True, min=20, max=100)

    Generates some lorem ipsum for the template.  By default, five paragraphs
    of HTML are generated with each paragraph between 20 and 100 words.
    If html is False, regular text is returned.  This is useful to generate simple
    contents for layout testing.

.. function:: dict(\**items)

    A convenient alternative to dict literals.  ``{'foo': 'bar'}`` is the same
    as ``dict(foo='bar')``.

.. class:: cycler(\*items)

    Cycle through values by yielding them one at a time, then restarting
    once the end is reached.

    Similar to ``loop.cycle``, but can be used outside loops or across
    multiple loops. For example, render a list of folders and files in a
    list, alternating giving them "odd" and "even" classes.

    .. code-block:: html+jinja

        {% set row_class = cycler("odd", "even") %}
        <ul class="browser">
        {% for folder in folders %}
          <li class="folder {{ row_class.next() }}">{{ folder }}
        {% endfor %}
        {% for file in files %}
          <li class="file {{ row_class.next() }}">{{ file }}
        {% endfor %}
        </ul>

    :param items: Each positional argument will be yielded in the order
        given for each cycle.

    .. versionadded:: 2.1

    .. method:: current
        :property:

        Return the current item. Equivalent to the item that will be
        returned next time :meth:`next` is called.

    .. method:: next()

        Return the current item, then advance :attr:`current` to the
        next item.

    .. method:: reset()

        Resets the current item to the first item.

.. class:: joiner(sep=', ')

    A tiny helper that can be used to "join" multiple sections.  A joiner is
    passed a string and will return that string every time it's called, except
    the first time (in which case it returns an empty string).  You can
    use this to join things::

        {% set pipe = joiner("|") %}
        {% if categories %} {{ pipe() }}
            Categories: {{ categories|join(", ") }}
        {% endif %}
        {% if author %} {{ pipe() }}
            Author: {{ author() }}
        {% endif %}
        {% if can_edit %} {{ pipe() }}
            <a href="?action=edit">Edit</a>
        {% endif %}

    .. versionadded:: 2.1

.. class:: namespace(...)

    Creates a new container that allows attribute assignment using the
    ``{% set %}`` tag::

        {% set ns = namespace() %}
        {% set ns.foo = 'bar' %}

    The main purpose of this is to allow carrying a value from within a loop
    body to an outer scope.  Initial values can be provided as a dict, as
    keyword arguments, or both (same behavior as Python's `dict` constructor)::

        {% set ns = namespace(found=false) %}
        {% for item in items %}
            {% if item.check_something() %}
                {% set ns.found = true %}
            {% endif %}
            * {{ item.title }}
        {% endfor %}
        Found item having something: {{ ns.found }}

    .. versionadded:: 2.10


Extensions
----------

The following sections cover the built-in Jinja extensions that may be
enabled by an application.  An application could also provide further
extensions not covered by this documentation; in which case there should
be a separate document explaining said :ref:`extensions
<jinja-extensions>`.


.. _i18n-in-templates:

i18n
~~~~

If the :ref:`i18n-extension` is enabled, it's possible to mark text in
the template as translatable. To mark a section as translatable, use a
``trans`` block:

.. code-block:: jinja

    {% trans %}Hello, {{ user }}!{% endtrans %}

Inside the block, no statements are allowed, only text and simple
variable tags.

Variable tags can only be a name, not attribute access, filters, or
other expressions. To use an expression, bind it to a name in the
``trans`` tag for use in the block.

.. code-block:: jinja

    {% trans user=user.username %}Hello, {{ user }}!{% endtrans %}

To bind more than one expression, separate each with a comma (``,``).

.. code-block:: jinja

    {% trans book_title=book.title, author=author.name %}
    This is {{ book_title }} by {{ author }}
    {% endtrans %}

To pluralize, specify both the singular and plural forms separated by
the ``pluralize`` tag.

.. code-block:: jinja

    {% trans count=list|length %}
    There is {{ count }} {{ name }} object.
    {% pluralize %}
    There are {{ count }} {{ name }} objects.
    {% endtrans %}

By default, the first variable in a block is used to determine whether
to use singular or plural form. If that isn't correct, specify the
variable used for pluralizing as a parameter to ``pluralize``.

.. code-block:: jinja

    {% trans ..., user_count=users|length %}...
    {% pluralize user_count %}...{% endtrans %}

When translating blocks of text, whitespace and linebreaks result in
hard to read and error-prone translation strings. To avoid this, a trans
block can be marked as trimmed, which will replace all linebreaks and
the whitespace surrounding them with a single space and remove leading
and trailing whitespace.

.. code-block:: jinja

    {% trans trimmed book_title=book.title %}
        This is {{ book_title }}.
        You should read it!
    {% endtrans %}

This results in ``This is %(book_title)s. You should read it!`` in the
translation file.

If trimming is enabled globally, the ``notrimmed`` modifier can be used
to disable it for a block.

.. versionadded:: 2.10
   The ``trimmed`` and ``notrimmed`` modifiers have been added.

It's possible to translate strings in expressions with these functions:

-   ``gettext``: translate a single string
-   ``ngettext``: translate a pluralizable string
-   ``_``: alias for ``gettext``

You can print a translated string like this:

.. code-block:: jinja

    {{ _("Hello, World!") }}

To use placeholders, use the ``format`` filter.

.. code-block:: jinja

    {{ _("Hello, %(user)s!")|format(user=user.username) }}

Always use keyword arguments to ``format``, as other languages may not
use the words in the same order.

If :ref:`newstyle-gettext` calls are activated, using placeholders is
easier. Formatting is part of the ``gettext`` call instead of using the
``format`` filter.

.. sourcecode:: jinja

    {{ gettext('Hello World!') }}
    {{ gettext('Hello %(name)s!', name='World') }}
    {{ ngettext('%(num)d apple', '%(num)d apples', apples|count) }}

The ``ngettext`` function's format string automatically receives the
count as a ``num`` parameter in addition to the given parameters.


Expression Statement
~~~~~~~~~~~~~~~~~~~~

If the expression-statement extension is loaded, a tag called `do` is available
that works exactly like the regular variable expression (``{{ ... }}``); except
it doesn't print anything.  This can be used to modify lists::

    {% do navigation.append('a string') %}


Loop Controls
~~~~~~~~~~~~~

If the application enables the :ref:`loopcontrols-extension`, it's possible to
use `break` and `continue` in loops.  When `break` is reached, the loop is
terminated;  if `continue` is reached, the processing is stopped and continues
with the next iteration.

Here's a loop that skips every second item::

    {% for user in users %}
        {%- if loop.index is even %}{% continue %}{% endif %}
        ...
    {% endfor %}

Likewise, a loop that stops processing after the 10th iteration::

    {% for user in users %}
        {%- if loop.index >= 10 %}{% break %}{% endif %}
    {%- endfor %}

Note that ``loop.index`` starts with 1, and ``loop.index0`` starts with 0
(See: :ref:`for-loop`).


Debug Statement
~~~~~~~~~~~~~~~

If the :ref:`debug-extension` is enabled, a ``{% debug %}`` tag will be
available to dump the current context as well as the available filters
and tests. This is useful to see what's available to use in the template
without setting up a debugger.

.. code-block:: html+jinja

    <pre>{% debug %}</pre>

.. code-block:: text

    {'context': {'cycler': <class 'jinja2.utils.Cycler'>,
                 ...,
                 'namespace': <class 'jinja2.utils.Namespace'>},
     'filters': ['abs', 'attr', 'batch', 'capitalize', 'center', 'count', 'd',
                 ..., 'urlencode', 'urlize', 'wordcount', 'wordwrap', 'xmlattr'],
     'tests': ['!=', '<', '<=', '==', '>', '>=', 'callable', 'defined',
               ..., 'odd', 'sameas', 'sequence', 'string', 'undefined', 'upper']}


With Statement
~~~~~~~~~~~~~~

.. versionadded:: 2.3

The with statement makes it possible to create a new inner scope.
Variables set within this scope are not visible outside of the scope.

With in a nutshell::

    {% with %}
        {% set foo = 42 %}
        {{ foo }}           foo is 42 here
    {% endwith %}
    foo is not visible here any longer

Because it is common to set variables at the beginning of the scope,
you can do that within the `with` statement.  The following two examples
are equivalent::

    {% with foo = 42 %}
        {{ foo }}
    {% endwith %}

    {% with %}
        {% set foo = 42 %}
        {{ foo }}
    {% endwith %}

An important note on scoping here.  In Jinja versions before 2.9 the
behavior of referencing one variable to another had some unintended
consequences.  In particular one variable could refer to another defined
in the same with block's opening statement.  This caused issues with the
cleaned up scoping behavior and has since been improved.  In particular
in newer Jinja versions the following code always refers to the variable
`a` from outside the `with` block::

    {% with a={}, b=a.attribute %}...{% endwith %}

In earlier Jinja versions the `b` attribute would refer to the results of
the first attribute.  If you depend on this behavior you can rewrite it to
use the ``set`` tag::

    {% with a={} %}
        {% set b = a.attribute %}
    {% endwith %}

.. admonition:: Extension

   In older versions of Jinja (before 2.9) it was required to enable this
   feature with an extension.  It's now enabled by default.

.. _autoescape-overrides:

Autoescape Overrides
--------------------

.. versionadded:: 2.4

If you want you can activate and deactivate the autoescaping from within
the templates.

Example::

    {% autoescape true %}
        Autoescaping is active within this block
    {% endautoescape %}

    {% autoescape false %}
        Autoescaping is inactive within this block
    {% endautoescape %}

After an `endautoescape` the behavior is reverted to what it was before.

.. admonition:: Extension

   In older versions of Jinja (before 2.9) it was required to enable this
   feature with an extension.  It's now enabled by default.
