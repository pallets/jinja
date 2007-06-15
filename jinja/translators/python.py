# -*- coding: utf-8 -*-
"""
    jinja.translators.python
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module translates a jinja ast into python code.

    This translator tries hard to keep Jinja sandboxed. All security
    relevant calls are wrapped by methods defined in the environment.
    This affects:

    - method calls
    - attribute access
    - name resolution

    It also adds debug symbols used by the traceback toolkit implemented
    in `jinja.utils`.

    Implementation Details
    ======================

    Some of the semantics are handled directly in the translator in order
    to speed up the parsing process. For example the semantics for the
    `is` operator are handled here, changing this would require and
    additional traversing of the node tree in the parser. Thus the actual
    translation process can raise a `TemplateSyntaxError` too.

    It might sound strange but the translator tries to keep the generated
    code readable as much as possible. This simplifies debugging the Jinja
    core a lot. The additional processing overhead is just relevant for
    the translation process, the additional comments and whitespace won't
    appear in the saved bytecode.

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
from jinja.datastructure import TemplateStream
from jinja.utils import set, capture_generator


#: regular expression for the debug symbols
_debug_re = re.compile(r'^\s*\# DEBUG\(filename=(?P<filename>.*?), '
                       r'lineno=(?P<lineno>\d+)\)$')

# For Python versions without generator exit exceptions
try:
    GeneratorExit = GeneratorExit
except NameError:
    class GeneratorExit(Exception):
        pass

# For Pythons without conditional expressions
try:
    exec '0 if 0 else 0'
    have_conditional_expr = True
except SyntaxError:
    have_conditional_expr = False


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
        ctx = self._prepare(*args, **kwargs)
        try:
            return capture_generator(self.generate_func(ctx))
        except:
            self._debug(ctx, *sys.exc_info())

    def stream(self, *args, **kwargs):
        """Render a template as stream."""
        def proxy(ctx):
            try:
                for item in self.generate_func(ctx):
                    yield item
            except GeneratorExit:
                return
            except:
                self._debug(ctx, *sys.exc_info())
        return TemplateStream(proxy(self._prepare(*args, **kwargs)))

    def _prepare(self, *args, **kwargs):
        """Prepare the template execution."""
        # if there is no generation function we execute the code
        # in a new namespace and save the generation function and
        # debug information.
        env = self.environment
        if self.generate_func is None:
            ns = {'environment': env}
            exec self.code in ns
            self.generate_func = ns['generate']
            self._debug_info = ns['debug_info']
        return env.context_class(env, *args, **kwargs)

    def _debug(self, ctx, exc_type, exc_value, traceback):
        """Debugging Helper"""
        # just modify traceback if we have that feature enabled
        from traceback import print_exception
        print_exception(exc_type, exc_value, traceback)

        if self.environment.friendly_traceback:
            # hook the debugger in
            from jinja.debugger import translate_exception
            exc_type, exc_value, traceback = translate_exception(
                self, ctx, exc_type, exc_value, traceback)
        print_exception(exc_type, exc_value, traceback)

        raise exc_type, exc_value, traceback


class PythonTranslator(Translator):
    """
    Pass this translator a ast tree to get valid python code.
    """

    def __init__(self, environment, node):
        self.environment = environment
        self.node = node

        #: mapping to constants in the environment that are not
        #: converted to context lookups. this should improve
        #: performance and avoid accidentally screwing things up
        #: by rebinding essential constants.
        self.constants = {
            'true':                 'True',
            'false':                'False',
            'none':                 'None',
            'undefined':            'undefined_singleton'
        }

        #: bind the nodes to the callback functions. There are
        #: some missing! A few are specified in the `unhandled`
        #: mapping in order to disallow their usage, some of them
        #: will not appear in the jinja parser output because
        #: they are filtered out.
        self.handlers = {
            # jinja nodes
            nodes.Template:         self.handle_template,
            nodes.Text:             self.handle_template_text,
            nodes.DynamicText:      self.handle_dynamic_text,
            nodes.NodeList:         self.handle_node_list,
            nodes.ForLoop:          self.handle_for_loop,
            nodes.IfCondition:      self.handle_if_condition,
            nodes.Cycle:            self.handle_cycle,
            nodes.Print:            self.handle_print,
            nodes.Macro:            self.handle_macro,
            nodes.Call:             self.handle_call,
            nodes.Set:              self.handle_set,
            nodes.Filter:           self.handle_filter,
            nodes.Block:            self.handle_block,
            nodes.Include:          self.handle_include,
            nodes.Trans:            self.handle_trans,
            # python nodes
            ast.Name:               self.handle_name,
            ast.AssName:            self.handle_assign_name,
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
            ast.FloorDiv:           self.handle_floor_div,
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

        #: mapping of unsupported syntax elements.
        #: the value represents the feature name that appears
        #: in the exception.
        self.unsupported = {ast.ListComp: 'list comprehension'}

        #: because of python2.3 compatibility add generator
        #: expressions only to the list of unused features
        #: if it exists.
        if hasattr(ast, 'GenExpr'):
            self.unsupported[ast.GenExpr] = 'generator expression'

        #: if expressions are unsupported too (so far)
        if hasattr(ast, 'IfExp'):
            self.unsupported[ast.IfExp] = 'inline if expression'

    # -- public methods

    def process(environment, node):
        """
        The only public method. Creates a translator instance,
        translates the code and returns it in form of an
        `Template` instance.
        """
        translator = PythonTranslator(environment, node)
        filename = node.filename or '<template>'
        source = translator.translate()
        return Template(environment, compile(source, filename, 'exec'))
    process = staticmethod(process)

    # -- private helper methods

    def indent(self, text):
        """
        Indent the current text. This does only indent the
        first line.
        """
        return (' ' * (self.indention * 4)) + text

    def to_tuple(self, args):
        """
        Return a tuple repr without nested repr.
        """
        return '(%s%s)' % (
            ', '.join(args),
            len(args) == 1 and ',' or ''
        )

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
                                              n.lineno,
                                              n.filename)
                args = []
                for arg in n.args:
                    if arg.__class__ is ast.Keyword:
                        raise TemplateSyntaxError('keyword arguments for '
                                                  'filters are not supported.',
                                                  n.lineno,
                                                  n.filename)
                    args.append(self.handle_node(arg))
                if n.star_args is not None or n.dstar_args is not None:
                    raise TemplateSyntaxError('*args / **kwargs is not supported '
                                              'for filters', n.lineno,
                                              n.filename)
                filters.append('(%r, %s)' % (
                    n.node.name,
                    self.to_tuple(args)
                ))
            elif n.__class__ is ast.Name:
                filters.append('(%r, ())' % n.name)
            else:
                raise TemplateSyntaxError('invalid filter. filter must be a '
                                          'hardcoded function name from the '
                                          'filter namespace',
                                          n.lineno, n.filename)
        self.used_shortcuts.add('apply_filters')
        return 'apply_filters(%s, context, %s)' % (s, self.to_tuple(filters))

    def handle_node(self, node):
        """
        Handle one node. Resolves the correct callback functions defined
        in the callback mapping. This also raises the `TemplateSyntaxError`
        for unsupported syntax elements such as list comprehensions.
        """
        if node.__class__ in self.handlers:
            out = self.handlers[node.__class__](node)
        elif node.__class__ in self.unsupported:
            raise TemplateSyntaxError('unsupported syntax element %r found.'
                                      % self.unsupported[node.__class__],
                                      node.lineno, node.filename)
        else:
            raise AssertionError('unhandled node %r' % node.__class__)
        return out

    def reset(self):
        """
        Reset translation variables such as indention or cycle id
        """
        #: current level of indention
        self.indention = 0
        #: each {% cycle %} tag has a unique ID which increments
        #: automatically for each tag.
        self.last_cycle_id = 0
        #: set of used shortcuts jinja has to make local automatically
        self.used_shortcuts = set(['undefined_singleton'])
        #: set of used datastructures jinja has to import
        self.used_data_structures = set()
        #: set of used utils jinja has to import
        self.used_utils = set()
        #: flags for runtime error
        self.require_runtime_error = False

    def translate(self):
        """
        Translate the node defined in the constructor after
        resetting the translator.
        """
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
        parent = None
        overwrites = {}
        blocks = {}
        requirements = []
        outer_filename = node.filename or '<template>'

        # this set is required in order to not add blocks to the block
        # dict a second time if they were not overridden in one template
        # in the template chain.
        already_registered_block = set()

        while node.extends is not None:
            # the direct child nodes in a template that are not blocks
            # are processed as template globals, thus executed *before*
            # the master layout template is loaded. This can be used
            # for further processing. The output of those nodes does
            # not appear in the final template.
            requirements += [child for child in node.getChildNodes()
                             if child.__class__ not in (nodes.Text,
                             nodes.Block, nodes.Extends)]

            # load the template we inherit from and add not known blocks
            parent = self.environment.loader.parse(node.extends.template,
                                                   node.filename)
            # look up all block nodes in the current template and
            # add them to the override dict.
            for n in get_nodes(nodes.Block, node):
                overwrites[n.name] = n
            # handle direct overrides
            for n in get_nodes(nodes.Block, parent):
                # an overwritten block for the parent template. handle that
                # override in the template and register it in the deferred
                # block dict.
                if n.name in overwrites and not n in already_registered_block:
                    blocks.setdefault(n.name, []).append(n.clone())
                    n.replace(overwrites[n.name])
                    already_registered_block.add(n)
            # make the parent node the new node
            node = parent

        # handle requirements code
        if requirements:
            requirement_lines = ['def bootstrap(context):']
            for n in requirements:
                requirement_lines.append(self.handle_node(n))
            requirement_lines.append('    if 0: yield None\n')

        # handle body in order to get the used shortcuts
        body_lines = [self.handle_node(n) for n in node]

        # same for blocks in callables
        block_lines = []
        block_items = blocks.items()
        block_items.sort()
        dict_lines = []
        for name, items in block_items:
            tmp = []
            for idx, item in enumerate(items):
                # ensure that the indention is correct
                self.indention = 1
                func_name = 'block_%s_%s' % (name, idx)
                data = self.handle_block(item, idx + 1)
                # blocks with data
                if data:
                    block_lines.extend([
                        'def %s(context):' % func_name,
                        self.indent(self.nodeinfo(item, True)),
                        data,
                        '    if 0: yield None\n'
                    ])
                    tmp.append('buffereater(%s)' % func_name)
                    self.used_utils.add('buffereater')
                # blocks without data, can default to something
                # from utils
                else:
                    tmp.append('empty_block')
                    self.used_utils.add('empty_block')
            dict_lines.append('    %r: %s' % (
                str(name),
                self.to_tuple(tmp)
            ))

        # bootstrapping code
        lines = ['# Essential imports', 'from __future__ import division']
        if self.used_utils:
            lines.append('from jinja.utils import %s' % ', '.join(self.used_utils))
        if self.require_runtime_error:
            lines.append('from jinja.exceptions import TemplateRuntimeError')
        if self.used_data_structures:
            lines.append('from jinja.datastructure import %s' % ', '.
                         join(self.used_data_structures))
        lines.append(
            '\n# Aliases for some speedup\n'
            '%s\n\n'
            '# Name for disabled debugging\n'
            '__name__ = %r\n\n'
            'def generate(context):\n'
            '    assert environment is context.environment' % (
                '\n'.join([
                    '%s = environment.%s' % (item, item) for item in
                    ['get_attribute', 'perform_test', 'apply_filters',
                     'call_function', 'call_function_simple', 'finish_var',
                     'undefined_singleton'] if item in self.used_shortcuts
                ]),
                outer_filename
            )
        )

        # the template body
        if requirements:
            lines.append('    for item in bootstrap(context): pass')
        lines.extend(body_lines)
        lines.append('    if 0: yield None\n')

        # now write the bootstrapping (requirements) core if there is one
        if requirements:
            lines.append('# Bootstrapping code')
            lines.extend(requirement_lines)

        # blocks must always be defined. even if it's empty. some
        # features depend on it
        if block_lines:
            lines.append('# Superable blocks')
            lines.extend(block_lines)
        lines.append('# Block mapping')
        if dict_lines:
            lines.append('blocks = {\n%s\n}\n' % ',\n'.join(dict_lines))
        else:
            lines.append('blocks = {}\n')

        # now get the real source lines and map the debugging symbols
        debug_mapping = []
        file_mapping = {}
        last = None
        offset = -1
        sourcelines = ('\n'.join(lines)).splitlines()
        result = []

        for idx, line in enumerate(sourcelines):
            m = _debug_re.search(line)
            if m is not None:
                d = m.groupdict()
                filename = d['filename'] or None
                if isinstance(filename, unicode):
                    filename = filename.encode('utf-8')
                if filename in file_mapping:
                    file_id = file_mapping[filename]
                else:
                    file_id = file_mapping[filename] = 'F%d' % \
                                                       len(file_mapping)
                this = (file_id, int(d['lineno']))
                # if it's the same as the line before we ignore it
                if this != last:
                    debug_mapping.append('(%r, %s, %r)' % ((idx - offset,) + this))
                    last = this
                # for each debug symbol the line number and so the offset
                # changes by one.
                offset += 1
            else:
                result.append(line)

        # now print file mapping and debug info
        result.append('\n# Debug Information')
        file_mapping = file_mapping.items()
        file_mapping.sort(lambda a, b: cmp(a[1], b[1]))
        for filename, file_id in file_mapping:
            result.append('%s = %r' % (file_id, filename))
        result.append('debug_info = %s' % self.to_tuple(debug_mapping))
        return '\n'.join(result)

    def handle_template_text(self, node):
        """
        Handle data around nodes.
        """
        return self.indent(self.nodeinfo(node)) + '\n' +\
               self.indent('yield %r' % node.text)

    def handle_dynamic_text(self, node):
        """
        Like `handle_template_text` but for nodes of the type
        `DynamicText`.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))
        self.used_shortcuts.add('finish_var')

        write(self.nodeinfo(node))
        write('yield %r %% (' % node.format_string)
        self.indention += 1
        for var in node.variables:
            write(self.nodeinfo(var))
            write('finish_var(%s, context)' % self.handle_node(var.variable) + ',')
        self.indention -= 1
        write(')')

        return '\n'.join(buf)

    def handle_node_list(self, node):
        """
        In some situations we might have a node list. It's just
        a collection of multiple statements.

        If the nodelist was empty it will return an empty string
        """
        body = '\n'.join([self.handle_node(n) for n in node])
        if body:
            return self.indent(self.nodeinfo(node)) + '\n' + body
        return ''

    def handle_for_loop(self, node):
        """
        Handle a for loop. Pretty basic, just that we give the else
        clause a different behavior.
        """
        self.used_data_structures.add('LoopContext')
        buf = []
        write = lambda x: buf.append(self.indent(x))
        write(self.nodeinfo(node))
        write('context.push()')

        # recursive loops
        if node.recursive:
            write('def loop(seq):')
            self.indention += 1
            write('for %s in context[\'loop\'].push(seq):' %
                self.handle_node(node.item),
            )

        # simple loops
        else:
            write('context[\'loop\'] = loop = LoopContext(%s, '
                  'context[\'loop\'], None)' % self.handle_node(node.seq))
            write('for %s in loop:' %
                self.handle_node(node.item)
            )

        # handle real loop code
        self.indention += 1
        write(self.nodeinfo(node.body))
        if node.body:
            buf.append(self.handle_node(node.body))
        else:
            write('pass')
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
            write('if 0: yield None')
            self.indention -= 1
            write('context[\'loop\'] = LoopContext(None, context[\'loop\'], '
                  'buffereater(loop))')
            self.used_utils.add('buffereater')
            write('for item in loop(%s):' % self.handle_node(node.seq))
            self.indention += 1
            write('yield item')
            self.indention -= 1

        write('context.pop()')
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
            buf.append(self.handle_node(body) or self.indent('pass'))
            self.indention -= 1
        if node.else_ is not None:
            write('else:')
            self.indention += 1
            write(self.nodeinfo(node.else_))
            buf.append(self.handle_node(node.else_) or self.indent('pass'))
            self.indention -= 1
        return '\n'.join(buf)

    def handle_cycle(self, node):
        """
        Handle the cycle tag.
        """
        self.used_data_structures.add('CycleContext')
        name = '::cycle_%x' % self.last_cycle_id
        self.last_cycle_id += 1
        buf = []
        write = lambda x: buf.append(self.indent(x))

        write('if %r not in context.current:' % name)
        self.indention += 1
        write(self.nodeinfo(node))
        if node.seq.__class__ in (ast.Tuple, ast.List):
            write('context.current[%r] = CycleContext(%s)' % (
                name,
                self.to_tuple([self.handle_node(n) for n in node.seq.nodes])
            ))
            hardcoded = True
        else:
            write('context.current[%r] = CycleContext()' % name)
            hardcoded = False
        self.indention -= 1

        self.used_shortcuts.add('finish_var')
        if hardcoded:
            write('yield finish_var(context.current[%r].cycle(), '
                  'context)' % name)
        else:
            write('yield finish_var(context.current[%r].cycle(%s), '
                  'context)' % (
                name,
                self.handle_node(node.seq)
            ))

        return '\n'.join(buf)

    def handle_print(self, node):
        """
        Handle a print statement.
        """
        self.used_shortcuts.add('finish_var')
        return self.indent(self.nodeinfo(node)) + '\n' +\
               self.indent('yield finish_var(%s, context)' %
                           self.handle_node(node.variable))

    def handle_macro(self, node):
        """
        Handle macro declarations.
        """
        # sanity check for name
        if node.name == '_' or \
           node.name in self.constants:
            raise TemplateSyntaxError('cannot override %r' % node.name,
                                      node.lineno, node.filename)
        if node.name in self.constants:
            raise TemplateSyntaxError('you cannot name a macro %r',
                                      node.lineno,
                                      node.filename)

        buf = []
        write = lambda x: buf.append(self.indent(x))

        write('def macro(*args, **kw):')
        self.indention += 1
        write(self.nodeinfo(node))

        # collect macro arguments
        arg_items = []
        caller_overridden = False

        # if we have conditional expressions available in that python
        # build (for example cpython > 2.4) we can use them, they
        # will perform slightly better.
        if have_conditional_expr:
            arg_tmpl = '\'%(name)s\': args[%(pos)d] if argcount > %(pos)d ' \
                       'else %(default)s'
        # otherwise go with the and/or tuple hack:
        else:
            arg_tmpl = '\'%(name)s\': (argcount > %(pos)d and '\
                       '(args[%(pos)d],) or (%(default)s,))[0]'

        if node.arguments:
            varargs_init = '\'varargs\': args[%d:]' % len(node.arguments)
            write('argcount = len(args)')
            for idx, (name, n) in enumerate(node.arguments):
                arg_items.append(arg_tmpl % {
                    'name':     name,
                    'pos':      idx,
                    'default':  n is None and 'undefined_singleton' or
                                self.handle_node(n)
                })
                if name == 'caller':
                    caller_overridden = True
                elif name == 'varargs':
                    varargs_init = None
        else:
            varargs_init = '\'varargs\': args'

        if caller_overridden:
            write('kw.pop(\'caller\', None)')
        else:
            arg_items.append('\'caller\': kw.pop(\'caller\', undefined_singleton)')
        if varargs_init:
            arg_items.append(varargs_init)

        write('context.push({%s})' % ',\n              '.join([
            idx and self.indent(item) or item for idx, item
            in enumerate(arg_items)
        ]))

        # disallow any keyword arguments
        write('if kw:')
        self.indention += 1
        write('raise TemplateRuntimeError(\'%s got an unexpected keyword '
              'argument %%r\' %% iter(kw).next())' % node.name)
        self.require_runtime_error = True
        self.indention -= 1

        write(self.nodeinfo(node.body))
        data = self.handle_node(node.body)
        if data:
            buf.append(data)
        write('context.pop()')
        write('if 0: yield None')
        self.indention -= 1
        buf.append(self.indent('context[%r] = buffereater(macro)' %
                               node.name))
        self.used_utils.add('buffereater')

        return '\n'.join(buf)

    def handle_call(self, node):
        """
        Handle extended macro calls.
        """
        buf = []
        write = lambda x: buf.append(self.indent(x))

        write('def call(**kwargs):')
        self.indention += 1
        write('context.push(kwargs)')
        data = self.handle_node(node.body)
        if data:
            buf.append(data)
        write('context.pop()')
        write('if 0: yield None')
        self.indention -= 1
        write('yield ' + self.handle_call_func(node.expr,
              {'caller': 'buffereater(call)'}))
        self.used_utils.add('buffereater')

        return '\n'.join(buf)

    def handle_set(self, node):
        """
        Handle variable assignments.
        """
        if node.name == '_' or node.name in self.constants:
            raise TemplateSyntaxError('cannot override %r' % node.name,
                                      node.lineno, node.filename)
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
        write('context.push()')
        write(self.nodeinfo(node.body))
        data = self.handle_node(node.body)
        if data:
            buf.append(data)
        write('context.pop()')
        write('if 0: yield None')
        self.indention -= 1
        write('yield %s' % self.filter('buffereater(filtered)()',
                                       node.filters))
        self.used_utils.add('buffereater')
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

        self.used_data_structures.add('SuperBlock')
        buf = []
        write = lambda x: buf.append(self.indent(x))

        write(self.nodeinfo(node))
        write('context.push({\'super\': SuperBlock(%r, blocks, %r, context)})' % (
            str(node.name),
            level
        ))
        write(self.nodeinfo(node.body))
        buf.append(rv)
        write('context.pop()')
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
               self.indent('yield context.translate_func(%r, %r, %r, %s)' % (
            node.singular,
            node.plural,
            node.indicator,
            replacements
        ))

    # -- python nodes

    def handle_assign_name(self, node):
        """
        Handle name assignments.
        """
        if node.name == '_' or \
           node.name in self.constants:
            raise TemplateSyntaxError('cannot override %r' % node.name,
                                      node.lineno, node.filename)
        return 'context[%r]' % node.name

    def handle_name(self, node):
        """
        Handle name assignments and name retreivement.
        """
        if node.name in self.constants:
            return self.constants[node.name]
        elif node.name == '_':
            return 'context.translate_func'
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
                                          node.lineno,
                                          node.filename)
            elif node.ops[0][1].__class__ is ast.Name:
                args = []
                name = node.ops[0][1].name
            elif node.ops[0][1].__class__ is ast.CallFunc:
                n = node.ops[0][1]
                if n.node.__class__ is not ast.Name:
                    raise TemplateSyntaxError('invalid test. test must '
                                              'be a hardcoded function name '
                                              'from the test namespace',
                                              n.lineno,
                                              n.filename)
                name = n.node.name
                args = []
                for arg in n.args:
                    if arg.__class__ is ast.Keyword:
                        raise TemplateSyntaxError('keyword arguments for '
                                                  'tests are not supported.',
                                                  n.lineno,
                                                  n.filename)
                    args.append(self.handle_node(arg))
                if n.star_args is not None or n.dstar_args is not None:
                    raise TemplateSyntaxError('*args / **kwargs is not supported '
                                              'for tests', n.lineno,
                                              n.filename)
            else:
                raise TemplateSyntaxError('is operator requires a test name'
                                          ' as operand', node.lineno,
                                          node.filename)
            self.used_shortcuts.add('perform_test')
            return 'perform_test(context, %r, %s, %s, %s)' % (
                    name,
                    self.to_tuple(args),
                    self.handle_node(node.expr),
                    node.ops[0][0] == 'is not'
                )

        # normal operators
        buf = []
        buf.append(self.handle_node(node.expr))
        for op, n in node.ops:
            if op in ('is', 'is not'):
                raise TemplateSyntaxError('is operator must not be chained',
                                          node.lineno, node.filename)
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
            raise TemplateSyntaxError('attribute access requires one '
                                      'argument', node.lineno,
                                      node.filename)
        assert node.flags != 'OP_DELETE', 'wtf? do we support that?'
        if node.subs[0].__class__ is ast.Sliceobj:
            return '%s%s' % (
                self.handle_node(node.expr),
                self.handle_node(node.subs[0])
            )
        self.used_shortcuts.add('get_attribute')
        return 'get_attribute(%s, %s)' % (
            self.handle_node(node.expr),
            self.handle_node(node.subs[0])
        )

    def handle_getattr(self, node):
        """
        Handle hardcoded attribute access.
        """
        self.used_shortcuts.add('get_attribute')
        return 'get_attribute(%s, %r)' % (
            self.handle_node(node.expr),
            node.attrname
        )

    def handle_ass_tuple(self, node):
        """
        Tuple unpacking loops.
        """
        return self.to_tuple([self.handle_node(n) for n in node.nodes])

    def handle_bitor(self, node):
        """
        We use the pipe operator for filtering.
        """
        return self.filter(self.handle_node(node.nodes[0]), node.nodes[1:])

    def handle_call_func(self, node, extra_kwargs=None):
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
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        if not (args or kwargs or star_args or dstar_args or extra_kwargs):
            self.used_shortcuts.add('call_function_simple')
            return 'call_function_simple(%s, context)' % \
                   self.handle_node(node.node)
        self.used_shortcuts.add('call_function')
        return 'call_function(%s, context, %s, {%s}, %s, %s)' % (
            self.handle_node(node.node),
            self.to_tuple(args),
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

    def handle_floor_div(self, node):
        """
        Divide two items, return truncated result.
        """
        return '(%s // %s)' % (
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
        return '[%s]' % ':'.join([self.handle_node(n) for n in node.nodes])
