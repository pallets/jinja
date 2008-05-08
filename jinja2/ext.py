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
from jinja2.exceptions import TemplateAssertionError, TemplateSyntaxError
from jinja2.utils import contextfunction, import_string, Markup


# the only real useful gettext functions for a Jinja template.  Note
# that ugettext must be assigned to gettext as Jinja doesn't support
# non unicode strings.
GETTEXT_FUNCTIONS = ('_', 'gettext', 'ngettext')


class ExtensionRegistry(type):
    """Gives the extension a unique identifier."""

    def __new__(cls, name, bases, d):
        rv = type.__new__(cls, name, bases, d)
        rv.identifier = rv.__module__ + '.' + rv.__name__
        return rv


class Extension(object):
    """Extensions can be used to add extra functionality to the Jinja template
    system at the parser level.  This is a supported but currently
    undocumented interface.  Custom extensions are bound to an environment but
    may not store environment specific data on `self`.  The reason for this is
    that an extension can be bound to another environment (for overlays) by
    creating a copy and reassigning the `environment` attribute.

    As extensions are created by the environment they cannot accept any
    arguments for configuration.  One may want to work around that by using
    a factory function, but that is not possible as extensions are identified
    by their import name.  The correct way to configure the extension is
    storing the configuration values on the environment.  Because this way the
    environment ends up acting as central configuration storage the
    attributes may clash which is why extensions have to ensure that the names
    they choose for configuration are not too generic.  ``prefix`` for example
    is a terrible name, ``fragment_cache_prefix`` on the other hand is a good
    name as includes the name of the extension (fragment cache).
    """
    __metaclass__ = ExtensionRegistry

    #: if this extension parses this is the list of tags it's listening to.
    tags = set()

    def __init__(self, environment):
        self.environment = environment

    def bind(self, environment):
        """Create a copy of this extension bound to another environment."""
        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.environment = environment
        return rv

    def parse(self, parser):
        """If any of the :attr:`tags` matched this method is called with the
        parser as first argument.  The token the parser stream is pointing at
        is the name token that matched.  This method has to return one or a
        list of multiple nodes.
        """

    def attr(self, name, lineno=None):
        """Return an attribute node for the current extension.  This is useful
        to pass callbacks to template code::

            nodes.Call(self.attr('_my_callback'), args, kwargs, None, None)

        That would call `self._my_callback` when the template is evaluated.
        """
        return nodes.ExtensionAttribute(self.identifier, name, lineno=lineno)


class InternationalizationExtension(Extension):
    """This extension adds gettext support to Jinja2."""
    tags = set(['trans'])

    def __init__(self, environment):
        Extension.__init__(self, environment)
        environment.globals['_'] = contextfunction(lambda c, x: c['gettext'](x))
        environment.extend(
            install_gettext_translations=self._install,
            install_null_translations=self._install_null,
            uninstall_gettext_translations=self._uninstall,
            extract_translations=self._extract
        )

    def _install(self, translations):
        self.environment.globals.update(
            gettext=translations.ugettext,
            ngettext=translations.ungettext
        )

    def _install_null(self):
        self.environment.globals.update(
            gettext=lambda x: x,
            ngettext=lambda s, p, n: (n != 1 and (p,) or (s,))[0]
        )

    def _uninstall(self, translations):
        for key in 'gettext', 'ngettext':
            self.environment.globals.pop(key, None)

    def _extract(self, source, gettext_functions=GETTEXT_FUNCTIONS):
        if isinstance(source, basestring):
            source = self.environment.parse(source)
        return extract_from_ast(source, gettext_functions)

    def parse(self, parser):
        """Parse a translatable tag."""
        lineno = parser.stream.next().lineno

        # find all the variables referenced.  Additionally a variable can be
        # defined in the body of the trans block too, but this is checked at
        # a later state.
        plural_expr = None
        variables = {}
        while parser.stream.current.type is not 'block_end':
            if variables:
                parser.stream.expect('comma')

            # skip colon for python compatibility
            if parser.skip_colon():
                break

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

        # singular and plural
        else:
            ngettext = nodes.Name('ngettext', 'load')
            node = nodes.Call(ngettext, [
                nodes.Const(singular),
                nodes.Const(plural),
                plural_expr
            ], [], None, None)

        # mark the return value as safe if we are in an
        # environment with autoescaping turned on
        if self.environment.autoescape:
            node = nodes.MarkSafe(node)

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
        if extension is InternationalizationExtension:
            have_trans_extension = True
        extensions.append(extension)
    if not have_trans_extension:
        extensions.append(InternationalizationExtension)

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
        # with other spontaneus environments.  The rest of the
        # arguments are optimizer, undefined, finalize, autoescape,
        # loader, cache size and auto reloading setting
        True, Undefined, None, False, None, 0, False
    )

    node = environment.parse(fileobj.read().decode(encoding))
    for lineno, func, message in extract_from_ast(node, keywords):
        yield lineno, func, message, []


#: nicer import names
i18n = InternationalizationExtension
