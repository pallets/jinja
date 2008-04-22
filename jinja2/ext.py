# -*- coding: utf-8 -*-
"""
    jinja2.ext
    ~~~~~~~~~~

    Jinja extensions (EXPERIMENAL)

    The plan: i18n and caching becomes a parser extension. cache/endcache
    as well as trans/endtrans are not keyword and don't have nodes but
    translate into regular jinja nodes so that the person who writes such
    custom tags doesn't have to generate python code himself.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from jinja2 import nodes


class Extension(object):
    """Instances of this class store parser extensions."""

    #: if this extension parses this is the list of tags it's listening to.
    tags = set()

    def __init__(self, environment):
        self.environment = environment

    def update_globals(self, globals):
        """Called to inject runtime variables into the globals."""
        pass

    def parse(self, parser):
        """Called if one of the tags matched."""


class CacheExtension(Extension):
    """An example extension that adds cacheable blocks."""
    tags = set(['cache'])

    def parse(self, parser):
        lineno = parser.stream.next().lineno
        args = [parser.parse_expression()]
        if parser.stream.current.type is 'comma':
            parser.stream.next()
            args.append(parser.parse_expression())
        body = parser.parse_statements(('name:endcache',), drop_needle=True)
        return nodes.CallBlock(
            nodes.Call(nodes.Name('cache_support', 'load'), args, [], None, None),
            [], [], body
        )
