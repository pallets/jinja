# -*- coding: utf-8 -*-
"""
    jinja.translators.python
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module translates a jinja ast into python code.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import re
import sys
from compiler import ast
from jinja import nodes
from jinja.nodes import get_nodes
from jinja.parser import Parser
from jinja.exceptions import TemplateSyntaxError
from jinja.translators import Translator
from jinja.utils import translate_exception, capture_generator, \
     RUNTIME_EXCEPTION_OFFSET


#: regular expression for the debug symbols
_debug_re = re.compile(r'^\s*\# DEBUG\(filename=(?P<filename>.*?), '
                       r'lineno=(?P<lineno>\d+)\)$')


def _to_tuple(args):
    """
    Return a tuple repr without nested repr.
    """
    return '(%s%s)' % (
        ', '.join(args),
        len(args) == 1 and ',' or ''
    )


class Template(object):
    """
    Represents a finished template.
    """

    def __init__(self, environment, code):
        self.environment = environment
        self.code = code
        self.generate_func = None
        #: holds debug information
        self._debug_info = None
        #: unused in loader environments but used when a template
        #: is loaded from a string in order to be able to debug those too
        self._source = None

    def dump(self, stream=None):
        """Dump the template into python bytecode."""
        if stream is not None:
            from marshal import dump
            dump(self.code, stream)
        else:
            from marshal import dumps
            return dumps(self.code)

    def load(environment, data):
        """Load the template from python bytecode."""
        if isinstance(data, basestring):
            from marshal import loads
            code = loads(data)
        else:
            from marshal import load
            code = load(data)
        return Template(environment, code)
    load = staticmethod(load)

    def render(self, *args, **kwargs):
        """Render a template."""
        # if there is no generation function we execute the code
        # in a new namespace and save the generation function and
        # debug information.
        if self.generate_func is None:
            ns = {'environment': self.environment}
            exec self.code in ns
            self.generate_func = ns['generate']
            self._debug_info = ns['debug_info']
        ctx = self.environment.context_class(self.environment, *args, **kwargs)
        try:
            return capture_generator(self.generate_func(ctx))
        except:
            # debugging system:
            # on any exception we first get the current exception information
            # and skip the internal frames (currently either one (python2.5)
            # or two (python2.4 and lower)). After that we call a function
            # that creates a new traceback that is easier to debug.
            exc_type, exc_value, traceback = sys.exc_info()
            for _ in xrange(RUNTIME_EXCEPTION_OFFSET):
                traceback = traceback.tb_next
            traceback = translate_exception(self, exc_type, exc_value,
                                            traceback, ctx)
            raise exc_type, exc_value, traceback


class PythonTranslator(Translator):
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
            nodes.Set:              self.handle_set,
            nodes.Filter:           self.handle_filter,
            nodes.Block:            self.handle_block,
            nodes.Include:          self.handle_include,
            nodes.Trans:            self.handle_trans,
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

        self.require_translations = False

    # -- public methods

    def process(environment, node):
        translator = PythonTranslator(environment, node)
        filename = node.filename or '<template>'
        source = translator.translate()
        return Template(environment,
                        compile(source, filename, 'exec'))
    process = staticmethod(process)

    # -- private helper methods

    def indent(self, text):
        """
        Indent the current text.
        """
        return (' ' * (self.indention * 4)) + text

    def nodeinfo(self, node, force=False):
        """
        Return a comment that helds the node informations or None
        if there is no need to add a debug comment.
        """
        return '# DEBUG(filename=%s, lineno=%s)' % (
            node.filename or '',
            node.lineno
        )

    def filter(self, s, filter_nodes):
        """
        Apply a filter on an object that already is a python expression.
        Used to avoid redundant code in bitor and the filter directive.
        """
        filters = []
        for n in filter_nodes:
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
                    raise TemplateSyntaxError('*args / **kwargs is not supported '
                                              'for filters', n.lineno)
                filters.append('(%r, %s)' % (
                    n.node.name,
                    _to_tuple(args)
                ))
            elif n.__class__ is ast.Name:
                filters.append('(%r, ())' % n.name)
            else:
                raise TemplateSyntaxError('invalid filter. filter must be a '
                                          'hardcoded function name from the '
                                          'filter namespace',
                                          n.lineno)
        return 'apply_filters(%s, context, %s)' % (s, _to_tuple(filters))

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

    def reset(self):
        self.indention = 0
        self.last_cycle_id = 0

    def translate(self):
        self.reset()
        return self.handle_node(self.node)

    # -- jinja nodes

    def handle_template(self, node):
        """
        Handle the overall template node. This node is the first node and
        ensures that we get the bootstrapping code. It also knows about
        inheritance information. It only occours as outer node, never in
        the tree itself.
        """
        self.indention = 1

        # if there is a parent template we parse the parent template and
        # update the blocks there. Once this is done we drop the current
        # template in favor of the new one. Do that until we found the
        # root template.
        requirements_todo = []
        parent = None
        overwrites = {}
        blocks = {}

        while node.extends is not None:
            # handle all requirements but not those from the
            # root template. The root template renders everything so
            # there is no need for additional requirements
            if node not in requirements_todo:
                requirements_todo.append(node)

            # load the template we inherit from and add not known blocks
            parent = self.environment.loader.parse(node.extends.template,
                                                   node.filename)
            # look up all block nodes in the current template and
            # add them to the override dict
            for n in get_nodes(nodes.Block, node):
                overwrites[n.name] = n
            # handle direct overrides
            for n in get_nodes(nodes.Block, parent):
                # an overwritten block for the parent template. handle that
                # override in the template and register it in the deferred
                # block dict.
                if n.name in overwrites:
                    blocks.setdefault(n.name, []).append(n.clone())
                    n.replace(overwrites[n.name])
            # make the parent node the new node
            node = parent

        # look up requirements
        requirements = []
        for req in requirements_todo:
            for n in req:
                if n.__class__ in (nodes.Set, nodes.Macro, nodes.Include):
                    requirements.append(n)

        # aliases boilerplate
        aliases = ['%s = environment.%s' % (item, item) for item in
                   ['get_attribute', 'perform_test', 'apply_filters',
                    'call_function', 'call_function_simple', 'finish_var']]

        # bootstrapping code
        lines = [
            'from __future__ import division\n'
            'from jinja.datastructure import Undefined, LoopContext, '
            'CycleContext, SuperBlock\n'
            'from jinja.utils import buffereater\n'
            '%s\n'
            '__name__ = %r\n\n'
            'def generate(context):\n'
            '    assert environment is context.environment\n'
            '    ctx_push = context.push\n'
            '    ctx_pop = context.pop' % (
                '\n'.join(aliases),
                node.filename
            )
        ]

        # we have requirements? add them here.
        body_lines = []
        if requirements:
            for n in requirements:
                body_lines.append(self.handle_node(n))

        # the template body
        body_lines.extend([self.handle_node(n) for n in node])

        # add translation helpers if required
        if self.require_translations:
            lines.append(
                '    translator = environment.get_translator(context)\n'
                '    def translate(s, p=None, n=None, r=None):\n'
                '        if p is None:\n'
                '            return translator.gettext(s) % (r or {})\n'
                '        return translator.ngettext(s, p, r[n]) % (r or {})'
            )

        # add body lines and "generator hook"
        lines.extend(body_lines)
        lines.append('    if False:\n        yield None')

        # add the missing blocks
        block_items = blocks.items()
        block_items.sort()
        dict_lines = []
        for name, items in block_items:
            tmp = []
            for idx, item in enumerate(items):
                # ensure that the indention is correct
                self.indention = 1
                func_name = 'block_%s_%s' % (name, idx)
                lines.extend([
                    '\ndef %s(context):' % func_name,
                    '    ctx_push = context.push',
                    '    ctx_pop = context.pop',
                    '    if False:',
                    '        yield None'
                ])
                lines.append(self.indent(self.nodeinfo(item, True)))
                lines.append(self.handle_block(item, idx + 1))
                tmp.append('buffereater(%s)' % func_name)
            dict_lines.append('    %r: %s' % (
                str(name),
                _to_tuple(tmp)
            ))
        lines.append('\nblocks = {\n%s\n}' % ',\n'.join(dict_lines))

        # now get the real source lines and map the debugging symbols
        debug_mapping = []
        last = None
        offset = -1
        sourcelines = ('\n'.join(lines)).splitlines()
        result = []

        for idx, line in enumerate(sourcelines):
            m = _debug_re.search(line)
            if m is not None:
                d = m.groupdict()
                this = (d['filename'] or None, int(d['lineno']))
                # if it's the same as the line before we ignore it
                if this != last:
                    debug_mapping.append((idx - offset,) + this)
                    last = this
                # for each debug symbol the line number and so the offset
                # changes by one.
                offset += 1
            else:
                result.append(line)

        result.append('\ndebug_info = %r' % debug_mapping)
        return '\n'.join(result)

    def handle_template_text(self, node):
        """
        Handle data around nodes.
        """
        return self.indent(self.nodeinfo(node)) + '\n' +\
               self.indent('yield %r' % node.text)

    def handle_node_list(self, node):
        """
        In some situations we might have a node list. It's just
        a collection of multiple statements.
        """
        return '\n'.join([self.indent(self.nodeinfo(node))] +
                         [self.handle_node(n) for n in node])

    def handle_for_loop(self, node):
        """
        Handle a for loop. Pretty basic, just that we give the else
        clause a different behavior.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write(self.nodeinfo(node))
        write('ctx_push()')

        # recursive loops
        if node.recursive:
            write('def forloop(seq):')
            self.indention += 1
            write('for %s in context[\'loop\'].push(seq):' %
                self.handle_node(node.item),
            )

        # simple loops
        else:
            write('context[\'loop\'] = loop = LoopContext(%s, context[\'loop\'], None)' %
                  self.handle_node(node.seq))
            write('for %s in loop:' %
                self.handle_node(node.item)
            )

        # handle real loop code
        self.indention += 1
        write(self.nodeinfo(node.body))
        buf.append(self.handle_node(node.body) or self.indent('pass'))
        self.indention -= 1

        # else part of loop
        if node.else_:
            write('if not context[\'loop\'].iterated:')
            self.indention += 1
            write(self.nodeinfo(node.else_))
            buf.append(self.handle_node(node.else_) or self.indent('pass'))
            self.indention -= 1

        # call recursive for loop!
        if node.recursive:
            write('context[\'loop\'].pop()')
            write('if False:')
            self.indention += 1
            write('yield None')
            self.indention -= 2
            write('context[\'loop\'] = LoopContext(None, context[\'loop\'], buffereater(forloop))')
            write('for item in forloop(%s):' % self.handle_node(node.seq))
            self.indention += 1
            write('yield item')
            self.indention -= 1

        write('ctx_pop()')
        return '\n'.join(buf)

    def handle_if_condition(self, node):
        """
        Handle an if condition node.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write(self.nodeinfo(node))
        for idx, (test, body) in enumerate(node.tests):
            write('%sif %s:' % (
                idx and 'el' or '',
                self.handle_node(test)
            ))
            self.indention += 1
            write(self.nodeinfo(body))
            buf.append(self.handle_node(body))
            self.indention -= 1
        if node.else_ is not None:
            write('else:')
            self.indention += 1
            write(self.nodeinfo(node.else_))
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
        write(self.nodeinfo(node))
        if node.seq.__class__ in (ast.Tuple, ast.List):
            write('context.current[%r] = CycleContext(%s)' % (
                name,
                _to_tuple([self.handle_node(n) for n in node.seq.nodes])
            ))
            hardcoded = True
        else:
            write('context.current[%r] = CycleContext()' % name)
            hardcoded = False
        self.indention -= 1

        if hardcoded:
            write('yield finish_var(context.current[%r].cycle(), context)' % name)
        else:
            write('yield finish_var(context.current[%r].cycle(%s), context)' % (
                name,
                self.handle_node(node.seq)
            ))

        return '\n'.join(buf)

    def handle_print(self, node):
        """
        Handle a print statement.
        """
        return self.indent(self.nodeinfo(node)) + '\n' +\
               self.indent('yield finish_var(%s, context)' %
                           self.handle_node(node.variable))

    def handle_macro(self, node):
        """
        Handle macro declarations.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))

        write('def macro(*args):')
        self.indention += 1
        write(self.nodeinfo(node))

        if node.arguments:
            write('argcount = len(args)')
            tmp = []
            for idx, (name, n) in enumerate(node.arguments):
                tmp.append('\'%s\': (argcount > %d and (args[%d],) or (%s,))[0]' % (
                    name,
                    idx,
                    idx,
                    n is None and 'Undefined' or self.handle_node(n)
                ))
            write('ctx_push({%s})' % ', '.join(tmp))
        else:
            write('ctx_push()')

        write(self.nodeinfo(node.body))
        buf.append(self.handle_node(node.body))
        write('ctx_pop()')
        write('if False:')
        self.indention += 1
        write('yield False')
        self.indention -= 2
        buf.append(self.indent('context[%r] = buffereater(macro)' % node.name))

        return '\n'.join(buf)

    def handle_set(self, node):
        """
        Handle variable assignments.
        """
        return self.indent(self.nodeinfo(node)) + '\n' + \
               self.indent('context[%r] = %s' % (
            node.name,
            self.handle_node(node.expr)
        ))

    def handle_filter(self, node):
        """
        Handle filter sections.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write('def filtered():')
        self.indention += 1
        write('ctx_push()')
        write(self.nodeinfo(node.body))
        buf.append(self.handle_node(node.body))
        write('ctx_pop()')
        write('if False:')
        self.indention += 1
        write('yield None')
        self.indention -= 2
        write('yield %s' % self.filter('u\'\'.join(filtered())', node.filters))
        return '\n'.join(buf)

    def handle_block(self, node, level=0):
        """
        Handle blocks in the sourcecode. We only use them to
        call the current block implementation that is stored somewhere
        else.
        """
        rv = self.handle_node(node.body)
        if not rv:
            return ''

        buf = []
        write = lambda x: buf.append(self.indent(x))

        write(self.nodeinfo(node))
        write('ctx_push({\'super\': SuperBlock(%r, blocks, %r, context)})' % (
            str(node.name),
            level
        ))
        write(self.nodeinfo(node.body))
        buf.append(self.handle_node(node.body))
        write('ctx_pop()')
        return '\n'.join(buf)

    def handle_include(self, node):
        """
        Include another template at the current position.
        """
        tmpl = self.environment.loader.parse(node.template,
                                             node.filename)
        return self.handle_node_list(tmpl)

    def handle_trans(self, node):
        """
        Handle translations.
        """
        self.require_translations = True
        if node.replacements:
            replacements = []
            for name, n in node.replacements.iteritems():
                replacements.append('%r: %s' % (
                    name,
                    self.handle_node(n)
                ))
            replacements = '{%s}' % ', '.join(replacements)
        else:
            replacements = 'None'
        return self.indent(self.nodeinfo(node)) + '\n' +\
               self.indent('yield translate(%r, %r, %r, %s)' % (
            node.singular,
            node.plural,
            node.indicator,
            replacements
        ))

    # -- python nodes

    def handle_name(self, node):
        """
        Handle name assignments and name retreivement.
        """
        if node.name in self.constants:
            return self.constants[node.name]
        elif node.name == '_':
            self.require_translations = True
            return 'translate'
        return 'context[%r]' % node.name

    def handle_compare(self, node):
        """
        Any sort of comparison
        """
        # the semantic for the is operator is different.
        # for jinja the is operator performs tests and must
        # be the only operator
        if node.ops[0][0] in ('is', 'is not'):
            if len(node.ops) > 1:
                raise TemplateSyntaxError('is operator must not be chained',
                                          node.lineno)
            elif node.ops[0][1].__class__ is ast.Name:
                args = []
                name = node.ops[0][1].name
            elif node.ops[0][1].__class__ is ast.CallFunc:
                n = node.ops[0][1]
                if n.node.__class__ is not ast.Name:
                    raise TemplateSyntaxError('invalid test. test must '
                                              'be a hardcoded function name '
                                              'from the test namespace',
                                              n.lineno)
                name = n.node.name
                args = []
                for arg in n.args:
                    if arg.__class__ is ast.Keyword:
                        raise TemplateSyntaxError('keyword arguments for '
                                                  'tests are not supported.',
                                                  n.lineno)
                    args.append(self.handle_node(arg))
                if n.star_args is not None or n.dstar_args is not None:
                    raise TemplateSyntaxError('*args / **kwargs is not supported '
                                              'for tests', n.lineno)
            else:
                raise TemplateSyntaxError('is operator requires a test name'
                                          ' as operand', node.lineno)
            return 'perform_test(context, %r, %s, %s, %s)' % (
                    name,
                    _to_tuple(args),
                    self.handle_node(node.expr),
                    node.ops[0][0] == 'is not'
                )

        # normal operators
        buf = []
        buf.append(self.handle_node(node.expr))
        for op, n in node.ops:
            if op in ('is', 'is not'):
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
        return 'get_attribute(%s, %s)' % (
            self.handle_node(node.expr),
            self.handle_node(node.subs[0])
        )

    def handle_getattr(self, node):
        """
        Handle hardcoded attribute access.
        """
        return 'get_attribute(%s, %r)' % (
            self.handle_node(node.expr),
            node.attrname
        )

    def handle_ass_tuple(self, node):
        """
        Tuple unpacking loops.
        """
        return _to_tuple([self.handle_node(n) for n in node.nodes])

    def handle_bitor(self, node):
        """
        We use the pipe operator for filtering.
        """
        return self.filter(self.handle_node(node.nodes[0]), node.nodes[1:])

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
        if not (args or kwargs or star_args or dstar_args):
            return 'call_function_simple(%s, context)' % self.handle_node(node.node)
        return 'call_function(%s, context, %s, {%s}, %s, %s)' % (
            self.handle_node(node.node),
            _to_tuple(args),
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
            self.handle_node(n) for n in node.nodes
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
