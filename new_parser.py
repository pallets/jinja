from jinja2 import nodes


def lineno_from_parseinfo(parseinfo):
    return parseinfo.line + 1

def parse(ast):
    if isinstance(ast, list):
        return [parse(item) for item in ast]

    if isinstance(ast, str):
        return parse_output(ast)

    if 'type' in ast and ast['type'] == 'variable':
        return parse_print(ast)

    if 'block' in ast:
        return parse_block(ast)

    if 'start' in ast and 'end' in ast:
        return parse_block_pair(ast)

    return None

def parse_block(ast):
    if ast['block']['name'] == 'from':
        return parse_block_from(ast)

    return None

def parse_block_pair(ast):
    if ast['start']['name'] == 'with':
        return parse_block_with(ast)

    return None

def parse_block_from(ast):
    names = []
    parameters = ast['block']['parameters']

    if len(parameters) > 2:
        names = []#parameters[2:]

    from_import = nodes.FromImport(
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )
    from_import.template = parse_variable(parameters[0]['value'])
    from_import.names = names

    return from_import

def parse_block_with(ast):
    with_node = nodes.With(
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

    targets = []
    values = []

    for parameter in ast['start']['parameters']:
        if 'key' not in parameter:
            raise

        targets.append(parameter['key'])
        values.append(parse_variable(parameter['value']))

    with_node.targets = targets
    with_node.values = values
    with_node.body = parse(ast['contents'])

    return with_node

def parse_literal(ast):
    if 'literal_type' not in ast:
        raise

    literal_type = ast['literal_type']

    if literal_type == 'string':
        return nodes.Const(
            ''.join(ast['value']),
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )

def parse_output(ast):
    return nodes.Output(
        [nodes.TemplateData(ast)]
    )

def parse_print(ast):
    variable = ast['name']

    node = parse_variable(variable)

    return nodes.Output([node])

def parse_template(ast):
    return nodes.Template(parse(ast), lineno=1)

def parse_variable(ast, variable_context='load'):
    name = ast['variable']

    if 'literal_type' in name:
        node = parse_literal(name)
    else:
        node = nodes.Name(
            name,
            variable_context,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )

    for accessor_ast in ast['accessors']:
        node = parse_variable_accessor(node, accessor_ast)

    if ast['filters']:
        for filter_ast in ast['filters']:
            node = parse_variable_filter(node, filter_ast)

    return node

def parse_variable_accessor(node, ast):
    accessor_type = ast['accessor_type']

    if accessor_type == 'brackets':
        accessor_node = nodes.Getitem()
        accessor_node.arg = parse_variable(ast['parameter'])
    elif accessor_type == 'dot':
        accessor_node = nodes.Getattr()
        accessor_node.attr = ast['parameter']

    accessor_node.node = node
    accessor_node.ctx = "load"
    accessor_node.lineno = lineno_from_parseinfo(ast['parseinfo'])

    return accessor_node

def parse_variable_filter(node, ast):
    args = []
    kwargs = []
    dynamic_args = None
    dynamic_kwargs = None

    if 'arguments' in ast:
        for argument in ast['arguments']:
            value = parse_variable(argument['value'])

            if 'key' in argument:
                kwargs.append(
                    nodes.Keyword(argument['key'], value)
                )
            else:
                args.append(value)

    return nodes.Filter(
        node,
        ast['name'],
        args,
        kwargs,
        dynamic_args,
        dynamic_kwargs,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )
