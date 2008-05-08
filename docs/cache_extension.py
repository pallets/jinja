from jinja2 import nodes
from jinja2.ext import Extension


class CacheExtension(Extension):
    """Adds support for fragment caching to Jinja2."""
    tags = set(['cache'])

    def __init__(self, environment):
        Extension.__init__(self, environment)

        # default dummy implementations.  If the class does not implement
        # those methods we add some noop defaults.
        if not hasattr(environment, 'add_fragment_to_cache'):
            environment.add_fragment_to_cache = lambda n, v, t: None
        if not hasattr(environment, 'load_fragment_from_cache'):
            environment.load_fragment_from_cache = lambda n: None

    def parse(self, parser):
        # the first token is the token that started the tag.  In our case
        # we only listen to ``'cache'`` so this will be a name token with
        # `cache` as value.  We get the line number so that we can give
        # that line number to the nodes we create by hand.
        lineno = parser.stream.next().lineno

        # now we parse a single expression that is used as cache key.
        args = [parser.parse_expression()]

        # if there is a comma, someone provided the timeout.  parse the
        # timeout then
        if parser.stream.current.type is 'comma':
            parser.stream.next()
            args.append(parser.parse_expression())

        # otherwise set the timeout to `None`
        else:
            args.append(nodes.Const(None))

        # now we parse the body of the cache block up to `endcache` and
        # drop the needle (which would always be `endcache` in that case)
        body = parser.parse_statements(['name:endcache'], drop_needle=True)

        # now return a `CallBlock` node that calls our _cache_support
        # helper method on this extension.
        return nodes.CallBlock(
            nodes.Call(self.attr('_cache_support'), args, [], None, None),
            [], [], body
        ).set_lineno(lineno)

    def _cache_support(self, name, timeout, caller):
        """Helper callback."""
        # try to load the block from the cache
        rv = self.environment.load_fragment_from_cache(name)
        if rv is not None:
            return rv

        # if there is no fragment in the cache, render it and store
        # it in the cache.
        rv = caller()
        self.environment.add_fragment_to_cache(name, rv, timeout)
        return rv
