from tatsu.exceptions import FailedSemantics
from . import nodes
from .exceptions import TemplateSyntaxError


class JinjaSemantics(object):

    def block_expression_pair(self, ast):
        start_block = ast['start']
        end_block = ast['end']

        if start_block['name'] != end_block['name']:
            raise FailedSemantics()

        return ast


def lineno_from_parseinfo(parseinfo):
    return parseinfo.line + 1

def parse(ast):
    def merge_output(blocks):
        if len(blocks) < 2:
            return blocks

        for idx in range(len(blocks) - 1, 0, -1):
            block = blocks[idx]
            previous_block = blocks[idx - 1]

            if isinstance(block, nodes.Output) and isinstance(previous_block, nodes.Output):
                previous_block.nodes += block.nodes
                del blocks[idx]

        return blocks

    def merge_template_data(blocks):
        for block in blocks:
            if isinstance(block, nodes.Output):
                if len(block.nodes) < 2:
                    continue

                outputs = block.nodes

                for idx in range(len(outputs) - 1, 0, -1):
                    output = outputs[idx]
                    previous_output = outputs[idx - 1]

                    if isinstance(output, nodes.TemplateData) and isinstance(previous_output, nodes.TemplateData):
                        previous_output.data += output.data
                        del outputs[idx]

        return blocks

    def remove_none(blocks):
        return [block for block in blocks if block is not None]

    if isinstance(ast, list):
        blocks = [parse(item) for item in ast]
        return merge_template_data(merge_output(remove_none(blocks)))

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

    if block_name == 'extends':
        return parse_block_extends(ast)

    if block_name == 'from':
        return parse_block_from(ast)

    if block_name == 'import':
        return parse_block_import(ast)

    if block_name == 'include':
        return parse_block_include(ast)

    if block_name == 'print':
        return parse_block_print(ast)

    if block_name == 'set':
        return parse_block_set(ast)

    return None

def parse_block_pair(ast):
    block_name = ast['start']['name']

    if block_name == 'autoescape':
        return parse_block_autoescape(ast)

    if block_name == 'block':
        return parse_block_block(ast)

    if block_name == 'call':
        return parse_block_call(ast)

    if block_name == 'filter':
        return parse_block_filter(ast)

    if block_name == 'for':
        return parse_block_for(ast)

    if block_name == 'if':
        return parse_block_if(ast)

    if block_name == 'macro':
        return parse_block_macro(ast)

    if block_name == 'set':
        return parse_block_set(ast)

    if block_name == 'with':
        return parse_block_with(ast)

    return None

def parse_block_autoescape(ast):
    return nodes.Scope(
        [nodes.ScopedEvalContextModifier(
            [nodes.Keyword(
                'autoescape',
                parse_variable(ast['start']['parameters'][0]['value']),
                lineno=lineno_from_parseinfo(ast['start']['parameters'][0]['parseinfo'])
            )],
            parse(ast['contents']),
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )],
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_block(ast):
    name = parse_variable(ast['start']['parameters'][0]['value']).name
    scoped = False

    if len(ast['start']['parameters']) > 1:
        scoped = ast['start']['parameters'][-1]['value']['variable'] == 'scoped'

    return nodes.Block(
        name,
        parse(ast['contents']),
        scoped,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_call(ast):
    parameters = ast['start']['parameters']

    call = parse_variable(parameters[0]['value'])
    args = []
    defaults = []
    body = parse(ast['contents'])

    if 'name_call_parameters' in ast['start']:
        for arg in ast['start']['name_call_parameters']:
            args.append(parse_variable(arg['value'], variable_context='param'))

    return nodes.CallBlock(
        call,
        args,
        defaults,
        body,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_extends(ast):
    return nodes.Extends(
        parse_conditional_expression(ast['block']['parameters'][0]['value'])
    )

def parse_block_filter(ast):
    body = parse(ast['contents'])
    filter_parameter = ast['start']['parameters'][0]['value']

    filter_base = parse_variable(filter_parameter)

    if isinstance(filter_base, nodes.Filter):
        filter = filter_base
        while isinstance(filter.node, nodes.Filter):
            filter = filter.node

        args = []
        kwargs = []
        dynamic_args = None
        dynamic_kwargs = None

        inner_filter = filter.node

        if isinstance(inner_filter, nodes.Call):
            args = inner_filter.args
            kwargs = inner_filter.kwargs
            dynamic_args = inner_filter.dyn_args
            dynamic_kwargs = inner_filter.dyn_kwargs

            inner_filter = inner_filter.node

        inner_filter = nodes.Filter(
            None,
            inner_filter.name,
            args,
            kwargs,
            dynamic_args,
            dynamic_kwargs,
            lineno=inner_filter.lineno
        )
        filter.node = inner_filter

    return nodes.FilterBlock(
        body,
        filter_base,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_for(ast):
    target = None
    iter = None
    body = ast['contents']
    else_ = []
    test = None
    recursive = False

    block_parameters = ast['start']['parameters']

    if block_parameters[0]['value']['operator'] == 'in':
        block_parameters[0:1] = [
            {
                "value": block_parameters[0]['value']['left']
            },
            {
                "value": {
                    "variable": "in"
                }
            },
            {
                "value": block_parameters[0]['value']['right']
            },
        ]

    if block_parameters[1]['value']['variable'] != 'in':
        raise

    target = parse_variable(block_parameters[0]['value'], variable_context='store')
    iter = parse_variable(block_parameters[2]['value'])

    if len(block_parameters) > 3:
        if block_parameters[3]['value']['variable'] == 'if':
            test = parse_conditional_expression(block_parameters[4]['value'])

    if len(block_parameters) > 3:
        recursive = block_parameters[-1]['value']['variable'] == 'recursive'

    else_ = _split_contents_at_block(ast['contents'], 'else')

    if else_ is not None:
        body, _, else_ = else_
    else:
        else_ = []

    return nodes.For(
        target, iter, parse(body), parse(else_), test, recursive,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_from(ast):
    parameters = ast['block']['parameters']

    template = parse_variable(parameters[0]['value'])
    names = []
    with_context = _parse_import_context(parameters)

    if with_context is None:
        with_context = False
    else:
        del parameters[-2:]

    if len(parameters) > 1 and parameters[1]['value']['variable'] != 'import':
        raise TemplateSyntaxError(
            "Expecting 'import' but did not find it",
            lineno=lineno_from_parseinfo(parameters[1]['parseinfo'])
        )

    if len(parameters) == 2:
        raise TemplateSyntaxError(
            "expected token 'name', got 'end of statement block'",
            lineno=lineno_from_parseinfo(parameters[1]['parseinfo'])
        )

    def _variable_to_name(variable):
        if isinstance(variable, str):
            return variable

        if 'alias' in variable:
            return (
                variable['variable'],
                variable['alias']
            )

        return variable['variable']

    for parameter in parameters[2:]:
        if 'tuple' in parameter['value']:
            for variable in parameter['value']['tuple']:
                names.append(_variable_to_name(variable))
        else:
            names.append(_variable_to_name(parameter['value']))

    from_import = nodes.FromImport(
        template,
        names,
        with_context,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

    return from_import

def parse_block_if(ast):
    test = parse_conditional_expression(ast['start']['parameters'][0]['value'])
    body = ast['contents']
    elif_ = []

    else_ = _split_contents_at_block(body, 'else')

    if else_ is not None:
        body, _, else_ = else_
    else:
        else_ = []

    elif_contents = _split_contents_at_block(body, 'elif')

    if elif_contents is not None:
        body, _, _ = elif_contents

    while elif_contents is not None:
        _, elif_condition, elif_contents = elif_contents

        elif_parsed = _split_contents_at_block(elif_contents, 'elif')

        if elif_parsed is not None:
            elif_body, _, _ = elif_parsed
        else:
            elif_body = elif_contents

        elif_.append(
            nodes.If(
                parse_conditional_expression(elif_condition['block']['parameters'][0]['value']),
                parse(elif_body),
                [],
                [],
                lineno=lineno_from_parseinfo(elif_condition['parseinfo'])
            )
        )

        elif_contents = elif_parsed

    return nodes.If(
        test,
        parse(body),
        elif_,
        parse(else_),
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_import(ast):
    block_parameters = ast['block']['parameters']

    template = parse_variable(block_parameters[0]['value'])
    target = None
    with_context = _parse_import_context(block_parameters) or False

    if len(block_parameters) > 2 and block_parameters[1]['value']['variable'] == 'as':
        target = parse_variable(block_parameters[2]['value']).name

    return nodes.Import(
        template,
        target,
        with_context,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_include(ast):
    block_parameters = ast['block']['parameters']

    template = parse_conditional_expression(block_parameters[0]['value'])
    with_context = _parse_import_context(block_parameters)
    ignore_missing = False

    if with_context is None:
        with_context = True
    else:
        del block_parameters[-2:]

    if len(block_parameters) == 3:
        ignore_missing = True

        if block_parameters[1]['value']['variable'] != 'ignore' and block_parameters[2]['value']['variable'] != 'missing':
            raise

    return nodes.Include(
        template,
        with_context,
        ignore_missing,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_macro(ast):
    definition = parse_variable(ast['start']['parameters'][0]['value'])
    name = definition.node.name
    params = []
    defaults = []
    body = parse(ast['contents'])

    for arg in definition.args:
        arg.set_ctx('param')
        params.append(arg)

    for kwarg in definition.kwargs:
        params.append(
            nodes.Name(kwarg.key, 'param')
        )
        defaults.append(kwarg.value)

    return nodes.Macro(
        name,
        params,
        defaults,
        body,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_block_print(ast):
    node = parse_variable(ast['block']['parameters'][0])

    return nodes.Output([node])

def parse_block_set(ast):
    if 'block' in ast:
        assignment = ast['block']['parameters'][0]

        if isinstance(assignment['key'], str):
            key = nodes.Name(assignment['key'], 'store')
        else:
            key = parse_variable(assignment['key'], variable_context="store")

        return nodes.Assign(
            key,
            parse_variable(assignment['value']),
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif 'start' in ast:
        key = parse_variable(ast['start']['parameters'][0]['value'], variable_context="store")
        filter = None

        if isinstance(key, nodes.Filter):
            filter = key
            key = key.node
            filter.node = None

        return nodes.AssignBlock(
            key,
            filter,
            parse(ast['contents']),
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

        targets.append(nodes.Name(parameter['key'], 'param'))
        values.append(parse_variable(parameter['value']))

    with_node.targets = targets
    with_node.values = values
    with_node.body = parse(ast['contents'])

    return with_node

def parse_comment(ast):
    return

def parse_concatenate_expression(ast):
    vars = [
        parse_variable(var) for var in ast['concatenate']
    ]

    return nodes.Concat(
        vars,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression(ast):
    if 'variable' in ast:
        return parse_variable(ast)

    if 'concatenate' in ast:
        return parse_concatenate_expression(ast)

    if 'logical_operator' in ast:
        return parse_conditional_expression_logical(ast)

    if 'math_operator' in ast:
        return parse_conditional_expression_math(ast)

    if 'not' in ast:
        return parse_conditional_expression_not(ast)

    if 'operator' in ast:
        return parse_conditional_expression_operator(ast)

    if 'test_expression' in ast:
        return parse_conditional_expression_if(ast)

    if 'test_function' in ast:
        return parse_conditional_expression_test(ast)

    return None

def parse_conditional_expression_if(ast):
    test = parse_conditional_expression(ast['test_expression'])
    expr1 = parse_variable(ast['true_value'])
    expr2 = None

    if 'false_value' in ast:
        expr2 = parse_variable(ast['false_value'])

    return nodes.CondExpr(
        test,
        expr1,
        expr2,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression_logical(ast):
    node_class_map = {
        'and': nodes.And,
        'or': nodes.Or,
    }

    node_class = node_class_map[ast['logical_operator']]

    return node_class(
        parse_conditional_expression(ast['left']),
        parse_conditional_expression(ast['right']),
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression_math(ast):
    node_class_map = {
        '+': nodes.Add,
        '-': nodes.Sub,
        '*': nodes.Mul,
        '**': nodes.Pow,
        '/': nodes.Div,
        '//': nodes.FloorDiv,
        '%': nodes.Mod,
    }

    node_class = node_class_map[ast['math_operator']]

    return node_class(
        parse_conditional_expression(ast['left']),
        parse_conditional_expression(ast['right']),
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression_not(ast):
    return nodes.Not(
        parse_conditional_expression(ast['not']),
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression_operator(ast):
    operand_map = {
        '>': 'gt',
        '>=': 'gteq',
        '==': 'eq',
        '!=': 'ne',
        '<': 'lt',
        '<=': 'lteq',
    }

    expr = parse_variable(ast['left'])
    operator = operand_map.get(ast['operator'], ast['operator'])
    operands = []

    right = parse_conditional_expression(ast['right'])

    if isinstance(right, nodes.Compare):
        operands.append(
            nodes.Operand(
                operator,
                right.expr
            )
        )
        operands.extend(right.ops)
    else:

        operands.append(
            nodes.Operand(
                operator,
                right
            )
        )

    return nodes.Compare(
        expr,
        operands,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def parse_conditional_expression_test(ast):
    node = parse_conditional_expression(ast['test_variable'])
    test_function = parse_variable(ast['test_function'])

    args = []
    kwargs = []
    dynamic_args = None
    dynamic_kwargs = None

    if isinstance(test_function, nodes.Call):
        call = test_function

        name = call.node.name
        args = call.args
        kwargs = call.kwargs
        dynamic_args = call.dyn_args
        dynamic_kwargs = call.dyn_kwargs
    elif isinstance(test_function, nodes.Const):
        const_map = {
            None: 'none',
            True: 'true',
            False: 'false',
        }

        name = const_map[test_function.value]
    else:
        name = test_function.name


    if ast['test_function_parameter']:
        args = [
            parse_conditional_expression(ast['test_function_parameter'])
        ]

    test_node = nodes.Test(
        node,
        name,
        args,
        kwargs,
        dynamic_args,
        dynamic_kwargs,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

    if 'negated' in ast and ast['negated']:
        test_node = nodes.Not(
            test_node,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )

    return test_node

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
    elif literal_type == 'dictionary':
        if not ast['value']:
            ast['value'] = []


        items = [
            nodes.Pair(
                parse_literal(item['key']),
                parse_variable(item['value']),
                lineno=lineno_from_parseinfo(item['parseinfo'])
            )
            for item in ast['value']
        ]

        return nodes.Dict(
            items,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'none':
        return nodes.Const(
            None,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'list':
        if not ast['value']:
            ast['value'] = []

        items = [
            parse_variable(item) for item in ast['value']
        ]

        return nodes.List(
            items,
            lineno=lineno_from_parseinfo(ast['parseinfo'])
        )
    elif literal_type == 'tuple':
        if not ast['value']:
            ast['value'] = []

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

    node = parse_conditional_expression(variable)

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
        if isinstance(ast['parameter'], str):
            accessor_node = nodes.Getattr()
            accessor_node.attr = ast['parameter']
        else:
            accessor_node = nodes.Getitem()
            accessor_node.arg = parse_literal(ast['parameter'])
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
            if dynamic_kwargs is not None:
                raise

            if 'dynamic_keyword_argument' in argument:

                dynamic_kwargs = parse_variable(argument['dynamic_keyword_argument'])

                continue

            if dynamic_args is not None:
                raise

            if 'dynamic_argument' in argument:
                dynamic_args = parse_variable(argument['dynamic_argument'])

                continue

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

    variable = parse_variable(ast)

    filter_node = None
    last_filter = None
    start_variable = variable

    while not isinstance(variable, nodes.Name):
        if isinstance(variable, nodes.Call):
            last_filter = filter_node
            filter_node = variable

        variable = variable.node

    new_filter = nodes.Filter(
        node,
        variable.name,
        args,
        kwargs,
        dynamic_args,
        dynamic_kwargs,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

    if filter_node is not None:
        new_filter.args = filter_node.args
        new_filter.kwargs = filter_node.kwargs

    if last_filter is None:
        return new_filter

    last_filter.node = new_filter

    return last_filter

def parse_variable_tuple(ast, variable_context):
    identifiers = []

    for name in ast['tuple']:
        identifiers.append(nodes.Name(name, variable_context))

    return nodes.Tuple(
        identifiers,
        variable_context,
        lineno=lineno_from_parseinfo(ast['parseinfo'])
    )

def _parse_import_context(block_parameters):
    if block_parameters[-1]['value']['variable'] != 'context':
        return None

    if block_parameters[-2]['value']['variable'] not in ['with', 'without']:
        return None

    return block_parameters[-2]['value']['variable'] == 'with'

def _split_contents_at_block(contents, block_name):
    for index, expression in enumerate(contents):
        if 'block' in expression:
            if expression['block']['name'] == block_name:
                return (contents[:index], expression, contents[index + 1:])

    return None
