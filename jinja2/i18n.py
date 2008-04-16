# -*- coding: utf-8 -*-
"""
    jinja2.i18n
    ~~~~~~~~~~~

    i18n support for Jinja.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from jinja2 import nodes
from jinja2.parser import _statement_end_tokens
from jinja2.exceptions import TemplateAssertionError


def parse_trans(parser):
    """Parse a translatable tag."""
    lineno = parser.stream.expect('trans').lineno

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
    singular_names, singular = _parse_block(parser, True)
    if singular_names:
        referenced.update(singular_names)
        if plural_expr is None:
            plural_expr = nodes.Name(singular_names[0], 'load')

    # if we have a pluralize block, we parse that too
    if parser.stream.current.type is 'pluralize':
        have_plural = True
        parser.stream.next()
        if parser.stream.current.type is not 'block_end':
            plural_expr = parser.parse_expression()
        parser.stream.expect('block_end')
        plural_names, plural = _parse_block(parser, False)
        parser.stream.next()
        referenced.update(plural_names)
    else:
        parser.stream.next()
        parser.end_statement()

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
        if plural_expr is None:
            raise TemplateAssertionError('pluralize without variables',
                                         lineno, parser.filename)
        plural_expr = None

    if variables:
        variables = nodes.Dict([nodes.Pair(nodes.Const(x, lineno=lineno), y)
                                for x, y in variables.items()])
    else:
        vairables = None

    node = _make_node(singular, plural, variables, plural_expr)
    node.set_lineno(lineno)
    return node


def _parse_block(parser, allow_pluralize):
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
            if parser.stream.current.type is 'endtrans':
                break
            elif parser.stream.current.type is 'pluralize':
                if allow_pluralize:
                    break
                raise TemplateSyntaxError('a translatable section can have '
                                          'only one pluralize section',
                                          parser.stream.current.lineno,
                                          parser.filename)
            raise TemplateSyntaxError('control structures in translatable '
                                      'sections are not allowed.',
                                      parser.stream.current.lineno,
                                      parser.filename)
        else:
            assert False, 'internal parser error'

    return referenced, u''.join(buf)


def _make_node(singular, plural, variables, plural_expr):
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
