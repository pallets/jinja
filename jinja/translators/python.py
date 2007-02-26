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


class PythonTranslator(object):
    """
    Pass this translator a ast tree to get valid python code.
    """

    def __init__(self, environment, node):
        self.environment = environment
        self.node = node
        self.indention = 0
        self.last_pos = 0

        self.handlers = {
            # jinja nodes
            nodes.Text:             self.handle_template_text,
            nodes.NodeList:         self.handle_node_list,
            nodes.ForLoop:          self.handle_for_loop,
            nodes.IfCondition:      self.handle_if_condition,
            nodes.Print:            self.handle_print,
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
            ast.UnarySub:           self.handle_unary_sub,
            ast.Power:              self.handle_power,
            ast.Dict:               self.handle_dict,
            ast.List:               self.handle_list,
            ast.Tuple:              self.handle_list,
            ast.And:                self.handle_and,
            ast.Or:                 self.handle_or,
            ast.Not:                self.handle_not
        }

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
        else:
            raise AssertionError('unhandled node %r' % node.__class__)
        return out

    # -- jinja nodes

    def handle_node_list(self, node):
        """
        In some situations we might have a node list. It's just
        a collection of multiple statements.
        """
        self.last_pos = node.pos
        buf = []
        for n in node:
            buf.append(self.handle_node(n))
        return '\n'.join(buf)

    def handle_for_loop(self, node):
        """
        Handle a for loop. Pretty basic, just that we give the else
        clause a different behavior.
        """
        self.last_pos = node.pos
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write('context.push()')
        write('parent_loop = context[\'loop\']')
        write('loop_data = None')
        write('for (loop_data, %s) in environment.iterate(%s):' % (
            self.handle_node(node.item),
            self.handle_node(node.seq)
        ))
        self.indention += 1
        write('loop_data.parent = parent_loop')
        write('context[\'loop\'] = loop_data')
        buf.append(self.handle_node(node.body))
        self.indention -= 1
        if node.else_ is not None:
            write('if loop_data is None:')
            self.indention += 1
            buf.append(self.handle_node(node.else_))
            self.indention -= 1
        write('context.pop()')
        return '\n'.join(buf)

    def handle_if_condition(self, node):
        """
        Handle an if condition node.
        """
        self.last_pos = node.pos
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write('if %s:' % self.handle_node(node.test))
        self.indention += 1
        buf.append(self.handle_node(node.body))
        self.indention -= 1
        if node.else_ is not None:
            write('else:')
            self.indention += 1
            buf.append(self.handle_node(node.else_))
            self.indention -= 1
        return '\n'.join(buf)

    def handle_print(self, node):
        """
        Handle a print statement.
        """
        self.last_pos = node.pos
        return self.indent('write_var(%s)' % self.handle_node(node.variable))

    def handle_template_text(self, node):
        """
        Handle data around nodes.
        """
        self.last_pos = node.pos
        return self.indent('write(%r)' % node.text)

    # -- python nodes

    def handle_name(self, node):
        """
        Handle name assignments and name retreivement.
        """
        return 'context[%r]' % node.name

    def handle_compare(self, node):
        """
        Any sort of comparison
        """
        buf = []
        buf.append(self.handle_node(node.expr))
        for op, n in node.ops:
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
                                      self.last_pos)
        assert node.flags != 'OP_DELETE', 'wtf? do we support that?'
        return 'get_attribute(%s, %s)' % (
            self.handle_node(node.expr),
            self.handle_node(node.subs[0])
        )

    def handle_getattr(self, node):
        """
        Handle hardcoded attribute access. foo.bar
        """
        return 'get_attribute(%s, %r)' % (
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
        return 'environment.apply_filters(%s, [%s])' % (
            self.handle_node(node.nodes[0]),
            ', '.join([self.handle_node(n) for n in node.nodes[1:]])
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
            self.handle_node(n) for n in nodes
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

    def translate(self):
        self.indention = 1
        lines = [
            'def generate(environment, context, write, write_var=None):',
            '    """This function was automatically generated by',
            '    the jinja python translator. do not edit."""',
            '    if write_var is None:',
            '        write_var = write'
        ]
        lines.append(self.handle_node(self.node))
        return '\n'.join(lines)


def translate(environment, node):
    """
    Do the translation to python.
    """
    return PythonTranslator(environment, node).translate()
