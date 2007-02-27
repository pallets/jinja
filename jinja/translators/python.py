# -*- coding: utf-8 -*-
"""
    jinja.translators.python
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module translates a jinja ast into python code.

    :copyright: 2006 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from compiler import ast
from jinja import nodes
from jinja.exceptions import TemplateSyntaxError


class PythonTranslator(object):
    """
    Pass this translator a ast tree to get valid python code.
    """

    def __init__(self, environment, node):
        self.environment = environment
        self.node = node

        self.constants = {
            'true':                 'True',
            'false':                'False',
            'none':                 'None',
            'undefined':            'Undefined'
        }

        self.handlers = {
            # jinja nodes
            nodes.Template:         self.handle_template,
            nodes.Text:             self.handle_template_text,
            nodes.NodeList:         self.handle_node_list,
            nodes.ForLoop:          self.handle_for_loop,
            nodes.IfCondition:      self.handle_if_condition,
            nodes.Cycle:            self.handle_cycle,
            nodes.Print:            self.handle_print,
            nodes.Macro:            self.handle_macro,
            # used python nodes
            ast.Name:               self.handle_name,
            ast.AssName:            self.handle_name,
            ast.Compare:            self.handle_compare,
            ast.Const:              self.handle_const,
            ast.Subscript:          self.handle_subscript,
            ast.Getattr:            self.handle_getattr,
            ast.AssTuple:           self.handle_ass_tuple,
            ast.Bitor:              self.handle_bitor,
            ast.CallFunc:           self.handle_call_func,
            ast.Add:                self.handle_add,
            ast.Sub:                self.handle_sub,
            ast.Div:                self.handle_div,
            ast.Mul:                self.handle_mul,
            ast.Mod:                self.handle_mod,
            ast.UnaryAdd:           self.handle_unary_add,
            ast.UnarySub:           self.handle_unary_sub,
            ast.Power:              self.handle_power,
            ast.Dict:               self.handle_dict,
            ast.List:               self.handle_list,
            ast.Tuple:              self.handle_list,
            ast.And:                self.handle_and,
            ast.Or:                 self.handle_or,
            ast.Not:                self.handle_not,
            ast.Slice:              self.handle_slice,
            ast.Sliceobj:           self.handle_sliceobj
        }

        self.unsupported = {
            ast.ListComp:           'list comprehensions',
            ast.From:               'imports',
            ast.Import:             'imports',
        }
        if hasattr(ast, 'GenExpr'):
            self.unsupported.update({
                ast.GenExpr:        'generator expressions'
            })

        self.reset()

    def indent(self, text):
        """
        Indent the current text.
        """
        return (' ' * (self.indention * 4)) + text

    def handle_node(self, node):
        """
        Handle one node
        """
        if node.__class__ in self.handlers:
            out = self.handlers[node.__class__](node)
        elif node.__class__ in self.unsupported:
            raise TemplateSyntaxError('unsupported syntax element %r found.'
                                      % self.unsupported[node.__class__],
                                      node.lineno)
        else:
            raise AssertionError('unhandled node %r' % node.__class__)
        return out

    # -- jinja nodes

    def handle_template(self, node):
        """
        Handle a template node. Basically do nothing but calling the
        handle_node_list function.
        """
        return self.handle_node_list(node)

    def handle_template_text(self, node):
        """
        Handle data around nodes.
        """
        return self.indent('write(%r)' % node.text)

    def handle_node_list(self, node):
        """
        In some situations we might have a node list. It's just
        a collection of multiple statements.
        """
        buf = []
        for n in node:
            buf.append(self.handle_node(n))
        return '\n'.join(buf)

    def handle_for_loop(self, node):
        """
        Handle a for loop. Pretty basic, just that we give the else
        clause a different behavior.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write('context.push()')

        # recursive loops
        if node.recursive:
            write('def forloop(seq):')
            self.indention += 1
            write('context[\'loop\'].push(seq)')
            write('for %s in context[\'loop\']:' %
                self.handle_node(node.item),
            )

        # simple loops
        else:
            write('context[\'loop\'] = LoopContext(%s, context[\'loop\'], None)' %
                  self.handle_node(node.seq))
            write('for %s in context[\'loop\']:' %
                self.handle_node(node.item)
            )

        # handle real loop code
        self.indention += 1
        buf.append(self.handle_node(node.body))
        self.indention -= 1

        # else part of loop
        if node.else_ is not None:
            write('if not context[\'loop\'].iterated:')
            self.indention += 1
            buf.append(self.handle_node(node.else_))
            self.indention -= 1

        # call recursive for loop!
        if node.recursive:
            write('context[\'loop\'].pop()')
            self.indention -= 1
            write('context[\'loop\'] = LoopContext(None, context[\'loop\'], forloop)')
            write('forloop(%s)' % self.handle_node(node.seq))

        write('context.pop()')
        return '\n'.join(buf)

    def handle_if_condition(self, node):
        """
        Handle an if condition node.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        for idx, (test, body) in enumerate(node.tests):
            write('%sif %s:' % (
                idx and 'el' or '',
                self.handle_node(test)
            ))
            self.indention += 1
            buf.append(self.handle_node(body))
            self.indention -= 1
        if node.else_ is not None:
            write('else:')
            self.indention += 1
            buf.append(self.handle_node(node.else_))
            self.indention -= 1
        return '\n'.join(buf)

    def handle_cycle(self, node):
        """
        Handle the cycle tag.
        """
        name = '::cycle_%x' % self.last_cycle_id
        self.last_cycle_id += 1
        buf = []
        write = lambda x: buf.append(self.indent(x))

        write('if not %r in context.current:' % name)
        self.indention += 1
        if node.seq.__class__ in (ast.Tuple, ast.List):
            write('context.current[%r] = CycleContext([%s])' % (
                name,
                ', '.join([self.handle_node(n) for n in node.seq.nodes])
            ))
            hardcoded = True
        else:
            write('context.current[%r] = CycleContext()' % name)
            hardcoded = False
        self.indention -= 1

        if hardcoded:
            write('write_var(context.current[%r].cycle())' % name)
        else:
            write('write_var(context.current[%r].cycle(%s))' % (
                name,
                self.handle_node(node.seq)
            ))

        return '\n'.join(buf)

    def handle_print(self, node):
        """
        Handle a print statement.
        """
        return self.indent('write_var(%s)' % self.handle_node(node.variable))

    def handle_macro(self, node):
        """
        Handle macro declarations.
        """
        buf = []

        args = []
        for name, n in node.arguments:
            if n is None:
                args.append('%s=Undefined' % name)
            else:
                args.append('%s=%s' % (name, self.handle_node(n)))
        buf.append(self.indent('def macro(%s):' % ', '.join(args)))
        self.indention += 1
        buf.append(self.handle_node(node.body))
        self.indention -= 1
        buf.append(self.indent('context[%r] = macro' % node.name))

        return '\n'.join(buf)

    # -- python nodes

    def handle_name(self, node):
        """
        Handle name assignments and name retreivement.
        """
        if node.name in self.constants:
            return self.constants[node.name]
        return 'context[%r]' % node.name

    def handle_compare(self, node):
        """
        Any sort of comparison
        """
        # the semantic for the is operator is different.
        # for jinja the is operator performs tests and must
        # be the only operator
        if node.ops[0][0] == 'is':
            if len(node.ops) > 1:
                raise TemplateSyntaxError('is operator must not be chained',
                                          node.lineno)
            elif node.ops[0][1].__class__ is not ast.Name:
                raise TemplateSyntaxError('is operator requires a test name',
                                          ' as operand', node.lineno)
            return 'environment.perform_test(%s, context, %r)' % (
                self.handle_node(node.expr),
                node.ops[0][1].name
            )

        # normal operators
        buf = []
        buf.append(self.handle_node(node.expr))
        for op, n in node.ops:
            if op == 'is':
                raise TemplateSyntaxError('is operator must not be chained',
                                          node.lineno)
            buf.append(op)
            buf.append(self.handle_node(n))
        return ' '.join(buf)

    def handle_const(self, node):
        """
        Constant values in expressions.
        """
        return repr(node.value)

    def handle_subscript(self, node):
        """
        Handle variable based attribute access foo['bar'].
        """
        if len(node.subs) != 1:
            raise TemplateSyntaxError('attribute access requires one argument',
                                      node.lineno)
        assert node.flags != 'OP_DELETE', 'wtf? do we support that?'
        if node.subs[0].__class__ is ast.Sliceobj:
            return '%s[%s]' % (
                self.handle_node(node.expr),
                self.handle_node(node.subs[0])
            )
        return 'environment.get_attribute(%s, %s)' % (
            self.handle_node(node.expr),
            self.handle_node(node.subs[0])
        )

    def handle_getattr(self, node):
        """
        Handle hardcoded attribute access. foo.bar
        """
        return 'environment.get_attribute(%s, %r)' % (
            self.handle_node(node.expr),
            node.attrname
        )

    def handle_ass_tuple(self, node):
        """
        Tuple unpacking loops.
        """
        return '(%s)' % ', '.join([self.handle_node(n) for n in node.nodes])

    def handle_bitor(self, node):
        """
        We use the pipe operator for filtering.
        """
        filters = []
        for n in node.nodes[1:]:
            if n.__class__ is ast.CallFunc:
                if n.node.__class__ is not ast.Name:
                    raise TemplateSyntaxError('invalid filter. filter must '
                                              'be a hardcoded function name '
                                              'from the filter namespace',
                                              n.lineno)
                args = []
                for arg in n.args:
                    if arg.__class__ is ast.Keyword:
                        raise TemplateSyntaxError('keyword arguments for '
                                                  'filters are not supported.',
                                                  n.lineno)
                    args.append(self.handle_node(arg))
                if n.star_args is not None or n.dstar_args is not None:
                    raise TemplateSynaxError('*args / **kwargs is not supported '
                                             'for filters', n.lineno)
                if args:
                    args = ', ' + ', '.join(args)
                filters.append('environment.prepare_filter(%r%s)' % (
                    n.node.name,
                    args or ''
                ))
            elif n.__class__ is ast.Name:
                filters.append('environment.prepare_filter(%s)' %
                               self.handle_node(n))
            else:
                raise TemplateSyntaxError('invalid filter. filter must be a '
                                          'hardcoded function name from the '
                                          'filter namespace',
                                          n.lineno)
        return 'environment.apply_filters(%s, context, [%s])' % (
            self.handle_node(node.nodes[0]),
            ', '.join(filters)
        )

    def handle_call_func(self, node):
        """
        Handle function calls.
        """
        args = []
        kwargs = {}
        star_args = dstar_args = None
        if node.star_args is not None:
            star_args = self.handle_node(node.star_args)
        if node.dstar_args is not None:
            dstar_args = self.handle_node(node.dstar_args)
        for arg in node.args:
            if arg.__class__ is ast.Keyword:
                kwargs[arg.name] = self.handle_node(arg.expr)
            else:
                args.append(self.handle_node(arg))
        return 'environment.call_function(%s, [%s], {%s}, %s, %s)' % (
            self.handle_node(node.node),
            ', '.join(args),
            ', '.join(['%r: %s' % i for i in kwargs.iteritems()]),
            star_args,
            dstar_args
        )

    def handle_add(self, node):
        """
        Add two items.
        """
        return '(%s + %s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_sub(self, node):
        """
        Sub two items.
        """
        return '(%s - %s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_div(self, node):
        """
        Divide two items.
        """
        return '(%s / %s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_mul(self, node):
        """
        Multiply two items.
        """
        return '(%s * %s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_mod(self, node):
        """
        Apply modulo.
        """
        return '(%s %% %s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_unary_add(self, node):
        """
        One of the more or less unused nodes.
        """
        return '(+%s)' % self.handle_node(node.expr)

    def handle_unary_sub(self, node):
        """
        Make a number negative.
        """
        return '(-%s)' % self.handle_node(node.expr)

    def handle_power(self, node):
        """
        handle foo**bar
        """
        return '(%s**%s)' % (
            self.handle_node(node.left),
            self.handle_node(node.right)
        )

    def handle_dict(self, node):
        """
        Dict constructor syntax.
        """
        return '{%s}' % ', '.join([
            '%s: %s' % (
                self.handle_node(key),
                self.handle_node(value)
            ) for key, value in node.items
        ])

    def handle_list(self, node):
        """
        We don't know tuples, tuples are lists for jinja.
        """
        return '[%s]' % ', '.join([
            self.handle_node(n) for n in node.nodes
        ])

    def handle_and(self, node):
        """
        Handle foo and bar.
        """
        return ' and '.join([
            self.handle_node(n) for n in node.nodes
        ])

    def handle_or(self, node):
        """
        handle foo or bar.
        """
        return ' or '.join([
            self.handle_node(n) for n in self.nodse
        ])

    def handle_not(self, node):
        """
        handle not operator.
        """
        return 'not %s' % self.handle_node(node.expr)

    def handle_slice(self, node):
        """
        Slice access.
        """
        if node.lower is None:
            lower = ''
        else:
            lower = self.handle_node(node.lower)
        if node.upper is None:
            upper = ''
        else:
            upper = self.handle_node(node.upper)
        assert node.flags != 'OP_DELETE', 'wtf? shouldn\'t happen'
        return '%s[%s:%s]' % (
            self.handle_node(node.expr),
            lower,
            upper
        )

    def handle_sliceobj(self, node):
        """
        Extended Slice access.
        """
        args = []
        for n in node.nodes:
            args.append(self.handle_node(n))
        return '[%s]' % ':'.join(args)

    def reset(self):
        self.indention = 1
        self.last_cycle_id = 0

    def translate(self):
        return (
            'from jinja.datastructures import Undefined, LoopContext, CycleContext\n'
            'def generate(context, write, write_var=None):\n'
            '    environment = context.environment\n'
            '    if write_var is None:\n'
            '        write_var = lambda x: write(environment.finish_var(x))\n'
        ) + self.handle_node(self.node)


def translate(environment, node):
    """
    Do the translation to python.
    """
    return PythonTranslator(environment, node).translate()
