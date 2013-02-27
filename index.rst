public: yes

Welcome
=======

    Jinja2 is a full featured template engine for Python.  It has full
    unicode support, an optional integrated sandboxed execution
    environment, widely used and BSD licensed.

Jinja is Beautiful
------------------

::

    {% extends "layout.html" %}
    {% block body %}
      <ul>
      {% for user in users %}
        <li><a href="{{ user.url }}">{{ user.username }}</a></li>
      {% endfor %}
      </ul>
    {% endblock %}

And Powerful
------------

Jinja2 is one of the most used template engines for Python.  It is
inspired by Django's templating system but extends it with an expressive
language that gives template authors a more powerful set of tools.  On top
of that it adds sandboxed execution and optional automatic escaping for
applications where security is important.

It is internally based on Unicode and runs on a wide range of Python
versions from 2.4 to current versions including Python 3.

Wide Range of Features
----------------------

-   Sandboxed execution mode.  Every aspect of the template execution is
    monitored and explicitly whitelisted or blacklisted, whatever is
    preferred.  This makes it possible to execute untrusted templates.
-   powerful automatic HTML escaping system for cross site scripting
    prevention.
-   Template inheritance makes it possible to use the same or a similar
    layout for all templates.
-   High performance with just in time compilation to Python bytecode.
    Jinja2 will translate your template sources on first load into Python
    bytecode for best runtime performance.
-   Optional ahead-of-time compilation
-   Easy to debug with a debug system that integrates template compile and
    runtime errors into the standard Python traceback system.
-   Configurable syntax.  For instance you can reconfigure Jinja2 to
    better fit output formats such as LaTeX or JavaScript.
-   Template designer helpers.  Jinja2 ships with a wide range of useful
    little helpers that help solving common tasks in templates such as
    breaking up sequences of items into multiple columns and more.

Who uses it?
------------

-   `Mozilla <http://www.mozilla.org/>`_
-   `SourceForge <http://www.sourceforge.net/>`_
-   `Instagram <http://instagr.am/>`_
-   `NPR <http://www.npr.org/>`_
-   … and many more


Contribute
----------

Found a bug? Have a good idea for improving Jinja2? Head over to
`Jinja's new github <http://github.com/mitsuhiko/jinja2>`_ page and
create a new ticket or fork.  If you just want to chat with fellow
developers, visit the `IRC channel </community/#irc-channel>`_ or join the
`mailinglist </community/#mailinglist>`_. 

.. raw:: html

    <a href="http://github.com/mitsuhiko/jinja2"><img style="position: fixed; top: 0; right: 0; border: 0;"
       src="http://s3.amazonaws.com/github/ribbons/forkme_right_gray_6d6d6d.png" alt="Fork me on GitHub"></a>


.. _Flask: http://flask.pocoo.org/
.. _tipfy: http://www.tipfy.org/
