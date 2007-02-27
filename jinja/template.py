# -*- coding: utf-8 -*-
"""
    jinja.template
    ~~~~~~~~~~~~~~

    Template class.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

"""
from jinja.datastructure import Context


class Template(object):
    """
    Represents a finished template.
    """

    def __init__(self, environment, generate_func):
        self.environment = environment
        self.generate_func = generate_func

    def render(self, *args, **kwargs):
        result = []
        ctx = Context(self.environment, *args, **kwargs)
        self.generate_func(ctx, result.append)
        return u''.join(result)
