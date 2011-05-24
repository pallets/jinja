Frequently Asked Questions
==========================

This page answers some of the often asked questions about Jinja.

.. highlight:: html+jinja

Why is it called Jinja?
-----------------------

The name Jinja was chosen because it's the name of a Japanese temple and
temple and template share a similar pronunciation.  It is not named after
the city in Uganda.

How fast is it?
---------------

We really hate benchmarks especially since they don't reflect much.  The
performance of a template depends on many factors and you would have to
benchmark different engines in different situations.  The benchmarks from the
testsuite show that Jinja2 has a similar performance to `Mako`_ and is between
10 and 20 times faster than Django's template engine or Genshi.  These numbers
should be taken with tons of salt as the benchmarks that took these numbers
only test a few performance related situations such as looping.  Generally
speaking the performance of a template engine doesn't matter much as the
usual bottleneck in a web application is either the database or the application
code.

.. _Mako: http://www.makotemplates.org/

How Compatible is Jinja2 with Django?
-------------------------------------

The default syntax of Jinja2 matches Django syntax in many ways.  However
this similarity doesn't mean that you can use a Django template unmodified
in Jinja2.  For example filter arguments use a function call syntax rather
than a colon to separate filter name and arguments.  Additionally the
extension interface in Jinja is fundamentally different from the Django one
which means that your custom tags won't work any longer.

Generally speaking you will use much less custom extensions as the Jinja
template system allows you to use a certain subset of Python expressions
which can replace most Django extensions.  For example instead of using
something like this::

    {% load comments %}
    {% get_latest_comments 10 as latest_comments %}
    {% for comment in latest_comments %}
        ...
    {% endfor %}

You will most likely provide an object with attributes to retrieve
comments from the database::

    {% for comment in models.comments.latest(10) %}
        ...
    {% endfor %}

Or directly provide the model for quick testing::

    {% for comment in Comment.objects.order_by('-pub_date')[:10] %}
        ...
    {% endfor %}

Please keep in mind that even though you may put such things into templates
it still isn't a good idea.  Queries should go into the view code and not
the template!

Isn't it a terrible idea to put Logic into Templates?
-----------------------------------------------------

Without a doubt you should try to remove as much logic from templates as
possible.  But templates without any logic mean that you have to do all
the processing in the code which is boring and stupid.  A template engine
that does that is shipped with Python and called `string.Template`.  Comes
without loops and if conditions and is by far the fastest template engine
you can get for Python.

So some amount of logic is required in templates to keep everyone happy.
And Jinja leaves it pretty much to you how much logic you want to put into
templates.  There are some restrictions in what you can do and what not.

Jinja2 neither allows you to put arbitrary Python code into templates nor
does it allow all Python expressions.  The operators are limited to the
most common ones and more advanced expressions such as list comprehensions
and generator expressions are not supported.  This keeps the template engine
easier to maintain and templates more readable.

Why is Autoescaping not the Default?
------------------------------------

There are multiple reasons why automatic escaping is not the default mode
and also not the recommended one.  While automatic escaping of variables
means that you will less likely have an XSS problem it also causes a huge
amount of extra processing in the template engine which can cause serious
performance problems.  As Python doesn't provide a way to mark strings as
unsafe Jinja has to hack around that limitation by providing a custom
string class (the :class:`Markup` string) that safely interacts with safe
and unsafe strings.

With explicit escaping however the template engine doesn't have to perform
any safety checks on variables.  Also a human knows not to escape integers
or strings that may never contain characters one has to escape or already
HTML markup.  For example when iterating over a list over a table of
integers and floats for a table of statistics the template designer can
omit the escaping because he knows that integers or floats don't contain
any unsafe parameters.

Additionally Jinja2 is a general purpose template engine and not only used
for HTML/XML generation.  For example you may generate LaTeX, emails,
CSS, JavaScript, or configuration files.

Why is the Context immutable?
-----------------------------

When writing a :func:`contextfunction` or something similar you may have
noticed that the context tries to stop you from modifying it.  If you have
managed to modify the context by using an internal context API you may
have noticed that changes in the context don't seem to be visible in the
template.  The reason for this is that Jinja uses the context only as
primary data source for template variables for performance reasons.

If you want to modify the context write a function that returns a variable
instead that one can assign to a variable by using set::

    {% set comments = get_latest_comments() %}

What is the speedups module and why is it missing?
--------------------------------------------------

To achieve a good performance with automatic escaping enabled, the escaping
function was also implemented in pure C in older Jinja2 releases and used if
Jinja2 was installed with the speedups module.

Because this feature itself is very useful for non-template engines as
well it was moved into a separate project on PyPI called `MarkupSafe`_.

Jinja2 no longer ships with a C implementation of it but only the pure
Python implementation.  It will however check if MarkupSafe is available
and installed, and if it is, use the Markup class from MarkupSafe.

So if you want the speedups, just import MarkupSafe.

.. _MarkupSafe: http://pypi.python.org/pypi/MarkupSafe

My tracebacks look weird.  What's happening?
--------------------------------------------

If the debugsupport module is not compiled and you are using a Python
installation without ctypes (Python 2.4 without ctypes, Jython or Google's
AppEngine) Jinja2 is unable to provide correct debugging information and
the traceback may be incomplete.  There is currently no good workaround
for Jython or the AppEngine as ctypes is unavailable there and it's not
possible to use the debugsupport extension.

Why is there no Python 2.3 support?
-----------------------------------

Python 2.3 is missing a lot of features that are used heavily in Jinja2.  This
decision was made as with the upcoming Python 2.6 and 3.0 versions it becomes
harder to maintain the code for older Python versions.  If you really need
Python 2.3 support you either have to use `Jinja 1`_ or other templating
engines that still support 2.3.

My Macros are overriden by something
------------------------------------

In some situations the Jinja scoping appears arbitrary:

layout.tmpl:

.. sourcecode:: jinja

    {% macro foo() %}LAYOUT{% endmacro %}
    {% block body %}{% endblock %}

child.tmpl:

.. sourcecode:: jinja

    {% extends 'layout.tmpl' %}
    {% macro foo() %}CHILD{% endmacro %}
    {% block body %}{{ foo() }}{% endblock %}

This will print ``LAYOUT`` in Jinja2.  This is a side effect of having
the parent template evaluated after the child one.  This allows child
templates passing information to the parent template.  To avoid this
issue rename the macro or variable in the parent template to have an
uncommon prefix.

.. _Jinja 1: http://jinja.pocoo.org/1/
