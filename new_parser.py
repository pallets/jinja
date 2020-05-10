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

    if 'raw' in ast:
        return parse_raw(ast)

    if 'comment' in ast:
        return parse_comment(ast)

    return None

def parse_block(ast):
    block_name = ast['block']['name']

    if block_name == 'from':
        return parse_block_from(ast)

    if block_name == 'set':
        return parse_block_set(ast)

    return None

def parse_block_pair(ast):
    block_name = ast['start']['name']

    if block_name == 'block':
        return parse_block_block(ast)

    if block_name == 'for':
        return parse_block_for(ast)

    if block_name == 'if':
        return parse_block_if(ast)

    if block_name == 'with':
        return parse_block_with(ast)

    return None

def parse_block_block(ast):
    name = parse_variable(ast['start']['parameters'][0]['value']).name
    scoped = False

    return nodes.Block(
        name,
        parse(ast['contents']),
        scoped,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_for(ast):
    target = None
    iter = None
    body = parse(ast['contents'])
    else_ = []
    test = None
    recursive = False

    block_parameters = ast['start']['parameters']

    if block_parameters[1]['value']['variable'] != 'in':
        raise

    target = parse_variable(block_parameters[0]['value'], variable_context='store')
    iter = parse_variable(block_parameters[2]['value'])

    if len(block_parameters) > 3:
        recursive = block_parameters[-1]['value']['variable'] == 'recursive'

    return nodes.For(
        target, iter, body, else_, test, recursive,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

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

def parse_block_if(ast):
    test = parse_conditional_expression(ast['start']['parameters'][0]['value'])
    body = parse(ast['contents'])
    elif_ = None
    else_ = None

    return nodes.If(
        test,
        body,
        elif_,
        else_,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_set(ast):
    if 'block' in ast:
        assignment = ast['block']['parameters'][0]

        if isinstance(assignment['key'], str):
            key = assignment['key']
        else:
            key = parse_variable(assignment['key'], variable_context="store")

        return nodes.Assign(
            key,
            parse_variable(assignment['value']),
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    return None

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

def parse_comment(ast):
    return

def parse_conditional_expression(ast):
    if 'variable' in ast:
        return parse_variable(ast)

    return None

def parse_literal(ast):
    if 'literal_type' not in ast:
        raise

    literal_type = ast['literal_type']

    if literal_type == 'boolean':
        return nodes.Const(
            ast['value'],
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'string':
        return nodes.Const(
            ''.join(ast['value']),
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'number':
        if 'fractional' not in ast and 'exponent' not in ast:
            const = int(ast['whole'])
        else:
            number = ast['whole']

            if 'fractional' in ast:
                number += '.' + ast['fractional']

            if 'exponent' in ast:
                number += 'e' + ast['exponent']

            const = float(number)

        return nodes.Const(
            const,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'list':
        items = [
            parse_literal(item) for item in ast['value']
        ]

        return nodes.List(
            items,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'tuple':
        items = [
            parse_literal(item) for item in ast['value']
        ]

        return nodes.Tuple(
            items,
            'load',
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    return None

def parse_output(ast):
    return nodes.Output(
        [nodes.TemplateData(ast)]
    )

def parse_print(ast):
    variable = ast['name']

    node = parse_variable(variable)

    return nodes.Output([node])

def parse_raw(ast):
    return parse_output(
        ''.join(ast['raw'])
    )

def parse_template(ast):
    return nodes.Template(parse(ast), lineno=1)

def parse_variable(ast, variable_context='load'):
    if 'tuple' in ast:
        return parse_variable_tuple(ast, variable_context)

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
    elif accessor_type == 'call':
        accessor_node = parse_variable_accessor_call(ast)

    accessor_node.node = node
    accessor_node.ctx = "load"
    accessor_node.lineno = lineno_from_parseinfo(ast['parseinfo'])

    return accessor_node

def parse_variable_accessor_call(ast):
    args = []
    kwargs = []
    dynamic_args = None
    dynamic_kwargs = None

    if ast['parameters']:
        for argument in ast['parameters']:
            value = parse_variable(argument['value'])

            if 'key' in argument:
                kwargs.append(
                    nodes.Keyword(argument['key'], value)
                )
            else:
                args.append(value)

    node = nodes.Call()
    node.args = args
    node.kwargs = kwargs
    node.dyn_args = dynamic_args
    node.dyn_kwargs = dynamic_kwargs

    return node

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

def parse_variable_tuple(ast, variable_context):
    identifiers = []

    for name in ast['tuple']:
        identifiers.append(nodes.Name(name, variable_context))

    return nodes.Tuple(
        identifiers,
        variable_context,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )
