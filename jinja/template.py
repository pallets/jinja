# -*- coding: utf-8 -*-
"""
    jinja.template
    ~~~~~~~~~~~~~~

    Template class.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

"""
from jinja.nodes import Node
from jinja.datastructure import Context
from jinja.translators.python import parse_and_translate, translate


def evaluate_source(source):
    """
    Evaluate a sourcecode and return the generate function.
    """
    ns = {}
    exec source in ns
    return ns['generate']


class Template(object):
    """
    Represents a finished template.
    """

    def __init__(self, environment, source):
        if isinstance(source, basestring):
            self.source = parse_and_translate(environment, source)
        elif isinstance(source, Node):
            self.source = translate(environment, source)
        else:
            raise TypeError('unsupported source type %r' %
                            source.__class__.__name__)
        self.environment = environment
        self.generate_func = None

    def render(self, *args, **kwargs):
        """
        Render a template.
        """
        if self.generate_func is None:
            self.generate_func = evaluate_source(self.source)
        result = []
        ctx = Context(self.environment, *args, **kwargs)
        self.generate_func(ctx, result.append)
        return u''.join(result)
