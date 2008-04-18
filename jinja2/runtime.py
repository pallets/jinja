# -*- coding: utf-8 -*-
"""
    jinja2.runtime
    ~~~~~~~~~~~~~~

    Runtime helpers.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
try:
    from collections import defaultdict
except ImportError:
    defaultdict = None
from jinja2.utils import Markup
from jinja2.exceptions import UndefinedError


__all__ = ['LoopContext', 'StaticLoopContext', 'TemplateContext',
           'Macro', 'IncludedTemplate', 'Markup']


class TemplateContext(dict):
    """Holds the variables of the local template or of the global one.  It's
    not save to use this class outside of the compiled code.  For example
    update and other methods will not work as they seem (they don't update
    the exported variables for example).
    """

    def __init__(self, environment, globals, name, blocks, standalone):
        dict.__init__(self, globals)
        self.environment = environment
        self.exported = set()
        self.name = name
        self.blocks = dict((k, [v]) for k, v in blocks.iteritems())

        # if the template is in standalone mode we don't copy the blocks over.
        # this is used for includes for example but otherwise, if the globals
        # are a template context, this template is participating in a template
        # inheritance chain and we have to copy the blocks over.
        if not standalone and isinstance(globals, TemplateContext):
            for name, parent_blocks in globals.blocks.iteritems():
                self.blocks.setdefault(name, []).extend(parent_blocks)

    def super(self, block):
        """Render a parent block."""
        try:
            func = self.blocks[block][-2]
        except LookupError:
            return self.environment.undefined('there is no parent block '
                                              'called %r.' % block)
        return SuperBlock(block, self, func)

    def __setitem__(self, key, value):
        """If we set items to the dict we track the variables set so
        that includes can access the exported variables."""
        dict.__setitem__(self, key, value)
        self.exported.add(key)

    def get_exported(self):
        """Get a dict of all exported variables."""
        return dict((k, self[k]) for k in self.exported)

    # if there is a default dict, dict has a __missing__ method we can use.
    if defaultdict is None:
        def __getitem__(self, name):
            if name in self:
                return self[name]
            return self.environment.undefined(name=name)
    else:
        def __missing__(self, name):
            return self.environment.undefined(name=name)

    def __repr__(self):
        return '<%s %s of %r>' % (
            self.__class__.__name__,
            dict.__repr__(self),
            self.name
        )


class SuperBlock(object):
    """When called this renders a parent block."""

    def __init__(self, name, context, render_func):
        self.name = name
        self._context = context
        self._render_func = render_func

    def __call__(self):
        return Markup(u''.join(self._render_func(self._context)))

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.name
        )


class IncludedTemplate(object):
    """Represents an included template."""

    def __init__(self, environment, context, template):
        template = environment.get_template(template)
        gen = template.root_render_func(context, standalone=True)
        context = gen.next()
        self._name = template.name
        self._rendered_body = u''.join(gen)
        self._context = context.get_exported()

    def __getitem__(self, name):
        return self._context[name]

    def __unicode__(self):
        return self._rendered_body

    def __html__(self):
        return self._rendered_body

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._name
        )


class LoopContextBase(object):
    """Helper for extended iteration."""

    def __init__(self, iterable, parent=None):
        self._iterable = iterable
        self._length = None
        self.index0 = 0
        self.parent = parent

    def cycle(self, *args):
        """A replacement for the old ``{% cycle %}`` tag."""
        if not args:
            raise TypeError('no items for cycling given')
        return args[self.index0 % len(args)]

    first = property(lambda x: x.index0 == 0)
    last = property(lambda x: x.revindex0 == 0)
    index = property(lambda x: x.index0 + 1)
    revindex = property(lambda x: x.length - x.index0)
    revindex0 = property(lambda x: x.length - x.index)

    def __len__(self):
        return self.length


class LoopContext(LoopContextBase):
    """A loop context for dynamic iteration."""

    def __init__(self, iterable, enforce_length=False):
        self._iterable = iterable
        self._next = iter(iterable).next
        self._length = None
        self.index0 = -1
        if enforce_length:
            len(self)

    def make_static(self):
        """Return a static loop context for the optimizer."""
        return StaticLoopContext(self.index0, self.length)

    def __iter__(self):
        return self

    def next(self):
        self.index0 += 1
        return self._next(), self

    @property
    def length(self):
        if self._length is None:
            try:
                length = len(self._iterable)
            except TypeError:
                self._iterable = tuple(self._iterable)
                self._next = iter(self._iterable).next
                length = len(tuple(self._iterable)) + self.index0 + 1
            self._length = length
        return self._length

    def __repr__(self):
        return 'LoopContext(%r)' % self.index0


class StaticLoopContext(LoopContextBase):
    """The static loop context is used in the optimizer to "freeze" the
    status of an iteration.  The only reason for this object is if the
    loop object is accessed in a non static way (eg: becomes part of a
    function call).
    """

    def __init__(self, index0, length):
        self.index0 = index0
        self.length = length

    def __repr__(self):
        """The repr is used by the optimizer to dump the object."""
        return 'StaticLoopContext(%r, %r)' % (
            self.index0,
            self.length
        )

    def make_static(self):
        return self


class Macro(object):
    """Wraps a macro."""

    def __init__(self, environment, func, name, arguments, defaults, catch_all, caller):
        self._environment = environment
        self._func = func
        self.name = name
        self.arguments = arguments
        self.defaults = defaults
        self.catch_all = catch_all
        self.caller = caller

    def __call__(self, *args, **kwargs):
        arg_count = len(self.arguments)
        if len(args) > arg_count:
            raise TypeError('macro %r takes not more than %d argument(s).' %
                            (self.name, len(self.arguments)))
        arguments = {}
        for idx, name in enumerate(self.arguments):
            try:
                value = args[idx]
            except IndexError:
                try:
                    value = kwargs.pop(name)
                except KeyError:
                    try:
                        value = self.defaults[idx - arg_count]
                    except IndexError:
                        value = self._environment.undefined(
                            'parameter %r was not provided' % name)
            arguments['l_' + name] = value
        if self.caller:
            caller = kwargs.pop('caller', None)
            if caller is None:
                caller = self._environment.undefined('No caller defined')
            arguments['l_caller'] = caller
        if self.catch_all:
            arguments['l_arguments'] = kwargs
        return self._func(**arguments)

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.name is None and 'anonymous' or repr(self.name)
        )


class Undefined(object):
    """The default undefined implementation.  This undefined implementation
    can be printed and iterated over, but every other access will raise a
    `NameError`.  Custom undefined classes must subclass this.
    """

    def __init__(self, hint=None, obj=None, name=None):
        self._undefined_hint = hint
        self._undefined_obj = obj
        self._undefined_name = name

    def _fail_with_error(self, *args, **kwargs):
        if self._undefined_hint is None:
            if self._undefined_obj is None:
                hint = '%r is undefined' % self._undefined_name
            elif not isinstance(self._undefined_name, basestring):
                hint = '%r object has no element %r' % (
                    self._undefined_obj.__class__.__name__,
                    self._undefined_name
                )
            else:
                hint = '%r object has no attribute %r' % (
                    self._undefined_obj.__class__.__name__,
                    self._undefined_name
                )
        else:
            hint = self._undefined_hint
        raise UndefinedError(hint)
    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
    __realdiv__ = __rrealdiv__ = __floordiv__ = __rfloordiv__ = \
    __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
    __getattr__ = __getitem__ = _fail_with_error

    def __unicode__(self):
        return u''

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return 'Undefined'

    def __len__(self):
        return 0

    def __iter__(self):
        if 0:
            yield None

    def __nonzero__(self):
        return False


class DebugUndefined(Undefined):
    """An undefined that returns the debug info when printed."""

    def __unicode__(self):
        if self._undefined_hint is None:
            if self._undefined_obj is None:
                return u'{{ %s }}' % self._undefined_name
            return '{{ no such element: %s[%r] }}' % (
                self._undefined_obj.__class__.__name__,
                self._undefined_name
            )
        return u'{{ undefined value printed: %s }}' % self._undefined_hint


class StrictUndefined(Undefined):
    """An undefined that barks on print and iteration as well as boolean tests.
    In other words: you can do nothing with it except checking if it's defined
    using the `defined` test.
    """

    __iter__ = __unicode__ = __len__ = __nonzero__ = Undefined._fail_with_error
