# -*- coding: utf-8 -*-
"""
    jinja
    ~~~~~

    Jinja is a `sandboxed`_ template engine written in pure Python. It
    provides a `Django`_ like non-XML syntax and compiles templates into
    executable python code. It's basically a combination of Django templates
    and python code.

    Nutshell
    --------

    Here a small example of a Jinja template::

        {% extends 'base.html' %}
        {% block title %}Memberlist{% endblock %}
        {% block content %}
          <ul>
          {% for user in users %}
            <li><a href="{{ user.url|e }}">{{ user.username|e }}</a></li>
          {% endfor %}
          </ul>
        {% endblock %}

    Philosophy
    ----------

    Application logic is for the controller but don't try to make the life
    for the template designer too hard by giving him too few functionality.

    For more informations visit the new `jinja webpage`_ and `documentation`_.

    Note
    ----

    This is the Jinja 1.0 release which is completely incompatible with the
    old "pre 1.0" branch. The old branch will still receive security updates
    and bugfixes but the 1.0 branch will be the only version that receives
    support.

    If you have an application that uses Jinja 0.9 and won't be updated in
    the near future the best idea is to ship a Jinja 0.9 checkout together
    with the application.

    The `Jinja trunk`_ is installable via `easy_install` with ``easy_install
    Jinja==dev``.

    .. _sandboxed: http://en.wikipedia.org/wiki/Sandbox_(computer_security)
    .. _Django: http://www.djangoproject.com/
    .. _jinja webpage: http://jinja.pocoo.org/
    .. _documentation: http://jinja.pocoo.org/documentation/index.html
    .. _Jinja trunk: http://trac.pocoo.org/repos/jinja/trunk#egg=Jinja-dev


    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from jinja.environment import Environment
from jinja.datastructure import Markup
from jinja.utils import from_string
from jinja.plugin import jinja_plugin_factory as template_plugin_factory
from jinja.loaders import FileSystemLoader, PackageLoader, DictLoader, \
     ChoiceLoader, FunctionLoader


__all__ = ['Environment', 'Markup', 'FileSystemLoader', 'PackageLoader',
           'DictLoader', 'ChoiceLoader', 'FunctionLoader', 'from_string',
           'template_plugin_factory']
