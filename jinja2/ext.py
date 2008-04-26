# -*- coding: utf-8 -*-
"""
    jinja2.ext
    ~~~~~~~~~~

    Jinja extensions allow to add custom tags similar to the way django custom
    tags work.  By default two example extensions exist: an i18n and a cache
    extension.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from collections import deque
from jinja2 import nodes
from jinja2.environment import get_spontaneous_environment
from jinja2.runtime import Undefined, concat
from jinja2.parser import statement_end_tokens
from jinja2.exceptions import TemplateAssertionError
from jinja2.utils import import_string


# the only real useful gettext functions for a Jinja template.  Note
# that ugettext must be assigned to gettext as Jinja doesn't support
# non unicode strings.
GETTEXT_FUNCTIONS = ('_', 'gettext', 'ngettext')


class Extension(object):
    """Instances of this class store parser extensions."""

    #: if this extension parses this is the list of tags it's listening to.
    tags = set()

    def __init__(self, environment):
        self.environment = environment

    def parse(self, parser):
        """Called if one of the tags matched."""


class CacheExtension(Extension):
    """An example extension that adds cacheable blocks."""
    tags = set(['cache'])

    def __init__(self, environment):
        Extension.__init__(self, environment)
        def dummy_cache_support(name, timeout=None, caller=None):
            if caller is not None:
                return caller()
        environment.globals['cache_support'] = dummy_cache_support

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


class TransExtension(Extension):
    """This extension adds gettext support to Jinja."""
    tags = set(['trans'])

    def __init__(self, environment):
        Extension.__init__(self, environment)
        environment.globals.update({
            '_':        lambda x: x,
            'gettext':  lambda x: x,
            'ngettext': lambda s, p, n: (s, p)[n != 1]
        })

    def parse(self, parser):
        """Parse a translatable tag."""
        lineno = parser.stream.next().lineno

        # skip colon for python compatibility
        if parser.stream.current.type is 'colon':
            parser.stream.next()

        # find all the variables referenced.  Additionally a variable can be
        # defined in the body of the trans block too, but this is checked at
        # a later state.
        plural_expr = None
        variables = {}
        while parser.stream.current.type is not 'block_end':
            if variables:
                parser.stream.expect('comma')
            name = parser.stream.expect('name')
            if name.value in variables:
                raise TemplateAssertionError('translatable variable %r defined '
                                             'twice.' % name.value, name.lineno,
                                             parser.filename)

            # expressions
            if parser.stream.current.type is 'assign':
                parser.stream.next()
                variables[name.value] = var = parser.parse_expression()
            else:
                variables[name.value] = var = nodes.Name(name.value, 'load')
            if plural_expr is None:
                plural_expr = var
        parser.stream.expect('block_end')

        plural = plural_names = None
        have_plural = False
        referenced = set()

        # now parse until endtrans or pluralize
        singular_names, singular = self._parse_block(parser, True)
        if singular_names:
            referenced.update(singular_names)
            if plural_expr is None:
                plural_expr = nodes.Name(singular_names[0], 'load')

        # if we have a pluralize block, we parse that too
        if parser.stream.current.test('name:pluralize'):
            have_plural = True
            parser.stream.next()
            if parser.stream.current.type is not 'block_end':
                plural_expr = parser.parse_expression()
            parser.stream.expect('block_end')
            plural_names, plural = self._parse_block(parser, False)
            parser.stream.next()
            referenced.update(plural_names)
        else:
            parser.stream.next()

        # register free names as simple name expressions
        for var in referenced:
            if var not in variables:
                variables[var] = nodes.Name(var, 'load')

        # no variables referenced?  no need to escape
        if not referenced:
            singular = singular.replace('%%', '%')
            if plural:
                plural = plural.replace('%%', '%')

        if not have_plural:
            plural_expr = None
        elif plural_expr is None:
            raise TemplateAssertionError('pluralize without variables',
                                         lineno, parser.filename)

        if variables:
            variables = nodes.Dict([nodes.Pair(nodes.Const(x, lineno=lineno), y)
                                    for x, y in variables.items()])
        else:
            variables = None

        node = self._make_node(singular, plural, variables, plural_expr)
        node.set_lineno(lineno)
        return node

    def _parse_block(self, parser, allow_pluralize):
        """Parse until the next block tag with a given name."""
        referenced = []
        buf = []
        while 1:
            if parser.stream.current.type is 'data':
                buf.append(parser.stream.current.value.replace('%', '%%'))
                parser.stream.next()
            elif parser.stream.current.type is 'variable_begin':
                parser.stream.next()
                name = parser.stream.expect('name').value
                referenced.append(name)
                buf.append('%%(%s)s' % name)
                parser.stream.expect('variable_end')
            elif parser.stream.current.type is 'block_begin':
                parser.stream.next()
                if parser.stream.current.test('name:endtrans'):
                    break
                elif parser.stream.current.test('name:pluralize'):
                    if allow_pluralize:
                        break
                    raise TemplateSyntaxError('a translatable section can '
                                              'have only one pluralize '
                                              'section',
                                              parser.stream.current.lineno,
                                              parser.filename)
                raise TemplateSyntaxError('control structures in translatable'
                                          ' sections are not allowed.',
                                          parser.stream.current.lineno,
                                          parser.filename)
            else:
                assert False, 'internal parser error'

        return referenced, concat(buf)

    def _make_node(self, singular, plural, variables, plural_expr):
        """Generates a useful node from the data provided."""
        # singular only:
        if plural_expr is None:
            gettext = nodes.Name('gettext', 'load')
            node = nodes.Call(gettext, [nodes.Const(singular)],
                              [], None, None)
            if variables:
                node = nodes.Mod(node, variables)

        # singular and plural
        else:
            ngettext = nodes.Name('ngettext', 'load')
            node = nodes.Call(ngettext, [
                nodes.Const(singular),
                nodes.Const(plural),
                plural_expr
            ], [], None, None)
            if variables:
                node = nodes.Mod(node, variables)
        return nodes.Output([node])


def extract_from_ast(node, gettext_functions=GETTEXT_FUNCTIONS):
    """Extract localizable strings from the given template node.

    For every string found this function yields a ``(lineno, function,
    message)`` tuple, where:

    * ``lineno`` is the number of the line on which the string was found,
    * ``function`` is the name of the ``gettext`` function used (if the
      string was extracted from embedded Python code), and
    *  ``message`` is the string itself (a ``unicode`` object, or a tuple
       of ``unicode`` objects for functions with multiple string arguments).
    """
    for node in node.find_all(nodes.Call):
        if not isinstance(node.node, nodes.Name) or \
           node.node.name not in gettext_functions:
            continue

        strings = []
        for arg in node.args:
            if isinstance(arg, nodes.Const) and \
               isinstance(arg.value, basestring):
                strings.append(arg.value)
            else:
                strings.append(None)

        if len(strings) == 1:
            strings = strings[0]
        else:
            strings = tuple(strings)
        yield node.lineno, node.node.name, strings


def babel_extract(fileobj, keywords, comment_tags, options):
    """Babel extraction method for Jinja templates.

    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should be
                     recognized as translation functions
    :param comment_tags: a list of translator tags to search for and include
                         in the results.  (Unused)
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)`` tuples.
             (comments will be empty currently)
    """
    encoding = options.get('encoding', 'utf-8')

    have_trans_extension = False
    extensions = []
    for extension in options.get('extensions', '').split(','):
        extension = extension.strip()
        if not extension:
            continue
        extension = import_string(extension)
        if extension is TransExtension:
            have_trans_extension = True
        extensions.append(extension)
    if not have_trans_extension:
        extensions.append(TransExtension)

    environment = get_spontaneous_environment(
        options.get('block_start_string', '{%'),
        options.get('block_end_string', '%}'),
        options.get('variable_start_string', '{{'),
        options.get('variable_end_string', '}}'),
        options.get('comment_start_string', '{#'),
        options.get('comment_end_string', '#}'),
        options.get('line_statement_prefix') or None,
        options.get('trim_blocks', '').lower() in ('1', 'on', 'yes', 'true'),
        tuple(extensions),
        # fill with defaults so that environments are shared
        # with other spontaneus environments.
        True, Undefined, unicode
    )

    node = environment.parse(fileobj.read().decode(encoding))
    for lineno, func, message in extract_from_ast(node, keywords):
        yield lineno, func, message, []
