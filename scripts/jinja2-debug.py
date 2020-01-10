#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Jinja Debug Interface
    ~~~~~~~~~~~~~~~~~~~~~

    Helper script for internal Jinja debugging.  Requires Werkzeug.

    :copyright: Copyright 2010 by Armin Ronacher.
    :license: BSD.
"""
from __future__ import print_function

import sys

from werkzeug import script

import jinja2

env = jinja2.Environment(
    extensions=[
        "jinja2.ext.i18n",
        "jinja2.ext.do",
        "jinja2.ext.loopcontrols",
        "jinja2.ext.with_",
        "jinja2.ext.autoescape",
    ],
    autoescape=True,
)


def shell_init_func():
    def _compile(x):
        print(env.compile(x, raw=True))

    result = {"e": env, "c": _compile, "t": env.from_string, "p": env.parse}
    for key in jinja2.__all__:
        result[key] = getattr(jinja2, key)
    return result


def action_compile():
    print(env.compile(sys.stdin.read(), raw=True))


action_shell = script.make_shell(shell_init_func)


if __name__ == "__main__":
    script.run()
