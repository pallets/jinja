======================
Designer Documentation
======================

This part of the Jinja documentaton is meant for template designers.

Basics
======

The Jinja template language is designed to strike a balance between content
and application logic. Nevertheless you can use a python like statement
language. You don't have to know how Python works to create Jinja templates,
but if you know it you can use some additional statements you may know from
Python.

Here is a small example template:

.. sourcecode:: html+jinja

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
    <head>
        <title>My Webpage</title>
    </head>
    <body>
        <ul id="navigation">
        {% for item in navigation %}
            <li><a href="{{ item.href|e }}">{{ item.caption|e }}</a></li>
        {% endfor %}
        </ul>

        <h1>My Webpage</h1>
        {{ variable }}
    </body>
    </html>

This covers the default settings. The application developer might have changed
the syntax from ``{% foo %}`` to ``<% foo %>`` or something similar. This
documentation just covers the default values.

A variable looks like ``{{ foobar }}`` where foobar is the variable name. Inside
of statements (``{% some content here %}``) variables are just normal names
without the braces around it. In fact ``{{ foobar }}`` is just an alias for
the statement ``{% print foobar %}``.

Variables are coming from the context provided by the application. Normally there
should be a documentation regarding the context contents but if you want to know
the content of the current context, you can add this to your template:

.. sourcecode:: html+jinja

    <pre>{{ debug()|e }}</pre>

A context isn't flat which means that each variable can has subvariables, as long
as it is representable as python data structure. You can access attributes of
a variable using the dot and bracket operators. The following examples show
this:

.. sourcecode:: jinja

    {{ user.username }}
        is the same as
    {{ user['username'] }}
        you can also use a variable to access an attribute:
    {{ users[current_user].username }}
        If you have numerical indices you have to use the [] syntax:
    {{ users[0].username }}

Filters
=======

In the examples above you might have noticed the pipe symbols. Pipe symbols tell
the engine that it has to apply a filter on the variable. Here is a small example:

.. sourcecode:: jinja

    {{ variable|replace('foo', 'bar')|escape }}

If you want, you can also put whitespace between the filters.

This will look for a variable `variable`, pass it to the filter `replace`
with the arguments ``'foo'`` and ``'bar'``, and pass the result to the filter
`escape` that automatically XML-escapes the value. The `e` filter is an alias for
`escape`. Here is the complete list of supported filters:

[[list_of_filters]]

.. admonition:: note

    Filters have a pretty low priority. If you want to add fitered values
    you have to put them into parentheses. The same applies if you want to access
    attributes:

    .. sourcecode:: jinja

        correct:
            {{ (foo|filter) + (bar|filter) }}
        wrong:
            {{ foo|filter + bar|filter }}

        correct:
            {{ (foo|filter).attribute }}
        wrong:
            {{ foo|filter.attribute }}

Tests
=====

You can use the `is` operator to perform tests on a value:

.. sourcecode:: jinja

    {{ 42 is numeric }} -> true
    {{ "foobar" is numeric }} -> false
    {{ 'FOO' is upper }} -> true

These tests are especially useful when used in `if` conditions.

[[list_of_tests]]

Global Functions
================

Test functions and filter functions live in their own namespace. Global
functions not. They behave like normal objects in the context. Beside the
functions added by the application or framewhere there are two functions
available per default:

`range`
    
    Works like the python `range function`_ just that it doesn't support
    ranges greater than ``1000000``.

`debug`

    Function that outputs the contents of the context.

Loops
=====

To iterate over a sequence, you can use the `for` loop. It basically looks like a
normal Python `for` loop and works pretty much the same:

.. sourcecode:: html+jinja

    <h1>Members</h1>
    <ul>
    {% for user in users %}
      <li>{{ loop.index }} / {{ loop.length }} - {{ user.username|escape }}</li>
    {% else %}
      <li><em>no users found</em></li>
    {% endfor %}
    </ul>

*Important* Contrary to Python is the optional ``else`` block only
executed if there was no iteration because the sequence was empty.

Inside of a `for` loop block you can access some special variables:

+----------------------+----------------------------------------+
| Variable             | Description                            |
+======================+========================================+
| `loop.index`         | The current iteration of the loop.     |
+----------------------+----------------------------------------+
| `loop.index0`        | The current iteration of the loop,     |
|                      | starting counting by 0.                |
+----------------------+----------------------------------------+
| `loop.revindex`      | The number of iterations from the end  |
|                      | of the loop.                           |
+----------------------+----------------------------------------+
| `loop.revindex0`     | The number of iterations from the end  |
|                      | of the loop, starting counting by 0.   |
+----------------------+----------------------------------------+
| `loop.first`         | True if first iteration.               |
+----------------------+----------------------------------------+
| `loop.last`          | True if last iteration.                |
+----------------------+----------------------------------------+
| `loop.even`          | True if current iteration is even.     |
+----------------------+----------------------------------------+
| `loop.odd`           | True if current iteration is odd.      |
+----------------------+----------------------------------------+
| `loop.length`        | Total number of items in the sequence. |
+----------------------+----------------------------------------+
| `loop.parent`        | The context of the parent loop.        |
+----------------------+----------------------------------------+

Loops also support recursion. Let's assume you have a sitemap where each item
might have a number of child items. A template for that could look like this:

.. sourcecode:: html+jinja

    <h1>Sitemap
    <ul id="sitemap">
    {% for item in sitemap recursive %}
      <li><a href="{{ item.url|e }}">{{ item.title|e }}</a>
      {% if item.children %}<ul>{{ loop(item.children) }}</ul>{% endif %}</li>
    {% endfor %}
    </ul>

What happens here? Basically the first thing that is different to a normal
loop is the additional ``recursive`` modifier in the `for`-loop declaration.
It tells the template engine that we want recursion. If recursion is enabled
the special `loop` variable is callable. If you call it with a sequence it will
automatically render the loop at that position with the new sequence as argument.

Cycling
=======

Sometimes you might want to have different text snippets for each row in a list,
for example to have alternating row colors. You can easily do this by using the
``{% cycle %}`` tag:

.. sourcecode:: html+jinja

    <ul id="messages">
    {% for message in messages %}
      <li class="{% cycle 'row1', 'row2' %}">{{ message|e }}</li>
    {% endfor %}
    </ul>

Each time Jinja encounters a `cycle` tag it will cycle through the list
of given items and return the next one. If you pass it one item jinja assumes
that this item is a sequence from the context and uses this:

.. sourcecode:: html+jinja

    <li style="color: {% cycle rowcolors %}">...</li>

Conditions
==========

Jinja supports Python-like `if` / `elif` / `else` constructs:

.. sourcecode:: jinja

    {% if user.active %}
        user {{ user.name|e }} is active.
    {% elif user.deleted %}
        user {{ user.name|e }} was deleted some time ago.
    {% else %}
        i don't know what's wrong with {{ user.username|e }}
    {% endif %}

If the user is active the first block is rendered. If not and the user was
deleted the second one, in all other cases the third one.

You can also use comparison operators:

.. sourcecode:: html+jinja

    {% if amount < 0 %}
        <span style="color: red">{{ amount }}</span>
    {% else %}
        <span style="color: black">{{ amount }}</span>
    {% endif %}

.. admonition:: Note

    Of course you can use `or` / `and` and parentheses to create more complex
    conditions, but usually the logic is already handled in the application and
    you don't have to create such complex constructs in the template code. However
    in some situations it might be a good thing to have the abilities to create
    them.

Operators
=========

Inside ``{{ variable }}`` blocks, `if` conditions and many other parts you can
can use expressions. In expressions you can use any of the following operators:

    ======= ===================================================================
    ``+``   add the right operand to the left one.
            ``{{ 1 + 2 }}`` would return ``3``.
    ``-``   subtract the right operand from the left one.
            ``{{ 1 - 1 }}`` would return ``0``.
    ``/``   divide the left operand by the right one.
            ``{{ 1 / 2 }}`` would return ``0.5``.
    ``*``   multiply the left operand with the right one.
            ``{{ 2 * 2 }}`` would return ``4``.
    ``**``  raise the left operand to the power of the right
            operand. ``{{ 2**3 }}`` would return ``8``.
    ``in``  perform sequence membership test. ``{{ 1 in [1,2,3] }}`` would
            return true.
    ``is``  perform a test on the value. See the section about
            tests for more information.
    ``|``   apply a filter on the value. See the section about
            filters for more information.
    ``and`` return true if the left and the right operand is true.
    ``or``  return true if the left or the right operand is true.
    ``not`` negate a statement (see below)
    ``()``  call a callable: ``{{ user.get_username() }}``. Inside of the
            parentheses you can use variables: ``{{ user.get(username) }}``.
    ======= ===================================================================

Note that there is no support for any bit operations or something similar.

* special note regarding `not`: The `is` and `in` operators support negation
  using an infix notation too: ``foo is not bar`` and ``foo not in bar``
  instead of ``not foo is bar`` and ``not foo in bar``. All other expressions
  require a prefix notation: ``not (foo and bar)``.

Boolean Values
==============

In If-Conditions Jinja performs a boolean check. All empty values (eg: empty
lists ``[]``, empty dicts ``{}`` etc) evaluate to `false`. Numbers that are
equal to `0`/`0.00` are considered `false` too. The boolean value of other
objects depends on the behavior the application developer gave it. Usually
items are `true`.

Here some examples that should explain it:

.. sourcecode:: jinja

    {% if [] %}
        will always be false because it's an empty list

    {% if {} %}
        false too.

    {% if ['foo'] %}
        this is true. Because the list is not empty.

    {% if "foobar" %}
        this is also true because the string is not empty.

Slicing
=======

Some objects support slicing operations. For example lists:

.. sourcecode:: jinja

    {% for item in items[:5] %}
        This will only iterate over the first 5 items of the list

    {% for item in items[5:10] %}
        This will only iterate from item 5 to 10.

    {% for item in items[:10:2] %}
        This will only yield items from start to ten and only returing
        even items.

For more informations about slicing have a look at the `slicing chapter`_
in the "Dive into Python" e-book.

Macros
======

If you want to use a partial template in more than one place, you might want to
create a macro from it:

.. sourcecode:: html+jinja

    {% macro show_user user %}
      <h1>{{ user.name|e }}</h1>
      <div class="test">
        {{ user.description }}
      </div>
    {% endmacro %}

Now you can use it from everywhere in the code by passing it an item:

.. sourcecode:: jinja
    
    {% for user in users %}
        {{ show_user(user) }}
    {% endfor %}

You can also specify more than one value:

.. sourcecode:: html+jinja

    {% macro show_dialog title, text %}
      <div class="dialog">
        <h1>{{ title|e }}</h1>
        <div class="test">{{ text|e }}</div>
      </div>
    {% endmacro %}

    {{ show_dialog('Warning', 'something went wrong i guess') }}

Inheritance
===========

The most powerful part of Jinja is template inheritance. Template inheritance
allows you to build a base "skeleton" template that contains all the common
elements of your site and defines **blocks** that child templates can override.

Sounds complicated but is very basic. It's easiest to understand it by starting
with an example.

Base Template
-------------

This template, which we'll call ``base.html``, defines a simple HTML skeleton
document that you might use for a simple two-column page. It's the job of
"child" templates to fill the empty blocks with content:

.. sourcecode:: html+jinja

    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
      <link rel="stylesheet" href="style.css" />
      <title>{% block title %}{% endblock %} - My Webpage</title>
      {% block html_head %}{% endblock %}
    </head>
    <body>
      <div id="content">
        {% block content %}{% endblock %}
      </div>

      <div id="footer">
        {% block footer %}
        &copy; Copyright 2006 by <a href="http://mydomain.tld">myself</a>.
        {% endblock %}
      </div>
    </body>

In this example, the ``{% block %}`` tags define four blocks that child templates
can fill in. All the `block` tag does is to tell the template engine that a
child template may override those portions of the template.

Child Template
--------------

A child template might look like this:

.. sourcecode:: html+jinja

    {% extends "base.html" %}
    {% block title %}Index{% endblock %}

    {% block html_head %}
      <style type="text/css">
        .important {
          color: #336699;
        }
      </style>
    {% endblock %}
    
    {% block content %}
        <h1>Index</h1>
        <p class="important">
          Welcome on my awsome homepage.
        </p>
    {% endblock %}

The ``{% extends %}`` tag is the key here. It tells the template engine that
this template "extends" another template. When the template system evaluates
this template, first it locates the parent.

The filename of the template depends on the template loader. For example the
``FileSystemLoader`` allows you to access other templates by giving the
filename. You can access templates in subdirectories with an slash:

.. sourcecode:: jinja

    {% extends "layout/default.html" %}

But this behavior can depend on the application using Jinja.

Note that since the child template didn't define the ``footer`` block, the
value from the parent template is used instead.

.. admonition:: Note

    You can't define multiple ``{% block %}`` tags with the same name in the
    same template. This limitation exists because a block tag works in "both"
    directions. That is, a block tag doesn't just provide a hole to fill - it
    also defines the content that fills the hole in the *parent*. If there were
    two similarly-named ``{% block %}`` tags in a template, that template's
    parent wouldn't know which one of the blocks' content to use.

Template Inclusion
==================

You can load another template at a given position using ``{% include %}``.
Usually it's a better idea to use inheritance but if you for example want to
load macros, `include` works better than `extends`:

.. sourcecode:: jinja

    {% include "myhelpers.html" %}
    {{ my_helper("foo") }}

If you define a macro called ``my_helper`` in ``myhelpers.html``, you can now
use it from the template as shown above.

Filtering Blocks
================

Sometimes it could be a good idea to filter a complete block of text. For
example, if you want to escape some html code:

.. sourcecode:: jinja

    {% filter escape %}
        <html>
          <code>goes here</code>
        </html>
    {% endfilter %}

Of course you can chain filters too:

.. sourcecode:: jinja

    {% filter lower|escape %}
        <B>SOME TEXT</B>
    {% endfilter %}

returns ``"&lt;b&gt;some text&lt;/b&gt;"``.

Defining Variables
==================

You can also define variables in the namespace using the ``{% set %}`` tag:

.. sourcecode:: jinja

    {% set foo = 'foobar' %}
    {{ foo }}

This should ouput ``foobar``.

Scopes
======

Jinja has multiple scopes. A scope is something like a new transparent foil on
a stack of foils. You can only write to the outermost foil but read all of them
since you can look through them. If you remove the top foil all data on that
foil disappears. Some tags in Jinja add a new layer to the stack. Currently
these are `block`, `for`, `macro` and `filter`. This means that variables and
other elements defined inside a macro, loop or some of the other tags listed
above will be only available in that block. Here an example:

.. sourcecode:: jinja

    {% macro angryhello name %}
      {% set angryname = name|upper %}
      Hello {{ name }}. Hello {{ name }}!
      HELLO {{ angryname }}!!!!!!111
    {% endmacro %}

The variable ``angryname`` just exists inside the macro, not outside it.

Defined macros appear on the context as variables. Because of this, they are
affected by the scoping too. A macro defined inside of a macro is just available
in those two macros (the macro itself and the macro it's defined in). For `set`
and `macro` two additional rules exist: If a macro is defined in an extended
template but outside of a visible block (thus outside of any block) will be
available in all blocks below. This allows you to use `include` statements to
load often used macros at once.

Undefined Variables
===================

If you have already worked with python you probably know about the fact that
undefined variables raise an exception. This is different in Jinja. There is a
special value called `undefined` that represents values that do not exist.

This special variable works complete different from any variables you maybe
know. If you print it using ``{{ variable }}`` it will not appear because it's
literally empty. If you try to iterate over it, it will work. But no items
are returned. Comparing this value to any other value results in `false`.
Even if you compare it to itself:

.. sourcecode:: jinja

    {{ undefined == undefined }}
        will return false. Not even undefined is undefined :)
        Use `is defined` / `is not defined`:

    {{ undefined is not defined }}
        will return true.

There are also some additional rules regarding this special value. Any
mathematical operators (``+``, ``-``, ``*``, ``/``) return the operand
as result:

.. sourcecode:: jinja

    {{ undefined + "foo" }}
        returns "foo"

    {{ undefined - 42 }}
        returns 42. Note: not -42!

In any expression `undefined` evaluates to `false`. It has no length, all
attribute calls return undefined, calling too:

.. sourcecode:: jinja

    {{ undefined.attribute().attribute_too[42] }}
        still returns `undefined`.

Escaping
========

Sometimes you might want to add Jinja syntax elements into the template
without executing them. In that case you have quite a few possibilities.

For small parts this might be a good way:

.. sourcecode:: jinja

    {{ "{{ foo }} is variable syntax and {% foo %} is block syntax" }}

When you have multiple elements you can use the ``raw`` block:

.. sourcecode:: jinja

    {% raw %}
        Filtering blocks works like this in Jinja:
        {% filter escape %}
            <html>
              <code>goes here</code>
            </html>
        {% endfilter %}
    {% endraw %}

Reserved Keywords
=================

Jinja has some keywords you cannot use a variable names. This limitation
exists to make look coherent. Syntax highlighters won't mess things up and
you will don't have unexpected output.

The following keywords exist and cannot be used as identifiers:

    `and`, `block`, `cycle`, `elif`, `else`, `endblock`, `endfilter`,
    `endfor`, `endif`, `endmacro`, `endraw`, `endtrans`, `extends`, `filter`,
    `for`, `if`, `in`, `include`, `is`, `macro`, `not`, `or`, `pluralize`,
    `raw`, `recursive`, `set`, `trans`

If you want to use such a name you have to prefix or suffix it or use
alternative names:

.. sourcecode:: jinja

    {% for macro_ in macros %}
        {{ macro_('foo') }}
    {% endfor %}

If future Jinja releases add new keywords those will be "light" keywords which
means that they won't raise an error for several releases but yield warnings
on the application side. But it's very unlikely that new keywords will be
added.

Internationalization
====================

If the application is configured for i18n, you can define translatable blocks
for translators using the `trans` tag or the special underscore function:

.. sourcecode:: jinja

    {% trans %}
        this is a translatable block
    {% endtrans %}

    {% trans "This is a translatable string" %}

    {{ _("This is a translatable string") }}

The latter one is useful if you want translatable arguments for filters etc.

If you want to have plural forms too, use the `pluralize` block:

.. sourcecode:: jinja

    {% trans users=users %}
        One user found.
    {% pluralize %}
        {{ users }} users found.
    {% endtrans %}

    {% trans first=(users|first).username|escape, user=users|length %}
        one user {{ first }} found.
    {% pluralize users %}
        {{ users }} users found, the first one is called {{ first }}.
    {% endtrans %}

If you have multiple arguments, the first one is assumed to be the indicator (the
number that is used to determine the correct singular or plural form. If you
don't have the indicator variable on position 1 you have to tell the `pluralize`
tag the correct variable name.

Inside translatable blocks you cannot use blocks or expressions (however you can
still use the ``raw`` block which will work as expected). The variable
print syntax (``{{ variablename }}``) is the only way to insert the variables
defined in the ``trans`` header. Filters must be applied in the header.

.. admonition:: note

    Please make sure that you always use pluralize blocks where required.
    Many languages have more complex plural forms than the English language.
    
    Never try to workaround that issue by using something like this:

    .. sourcecode:: jinja

        {% if count != 1 %}
            {{ count }} users found.
        {% else %}
            one user found.
        {% endif %}

.. _slicing chapter: http://diveintopython.org/native_data_types/lists.html#odbchelper.list.slice
.. _range function: http://docs.python.org/tut/node6.html#SECTION006300000000000000000
