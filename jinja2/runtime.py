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


__all__ = ['LoopContext', 'StaticLoopContext', 'TemplateContext',
           'Macro', 'IncludedTemplate', 'TemplateData']


class TemplateData(unicode):
    """Marks data as "coming from the template".  This is used to let the
    system know that this data is already processed if a finalization is
    used."""

    def __html__(self):
        return self


class TemplateContext(dict):
    """Holds the variables of the local template or of the global one.  It's
    not save to use this class outside of the compiled code.  For example
    update and other methods will not work as they seem (they don't update
    the exported variables for example).
    """

    def __init__(self, environment, globals, filename, blocks, standalone):
        dict.__init__(self, globals)
        self.environment = environment
        self.exported = set()
        self.filename = filename
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
            return self.environment.undefined('super',
                extra='there is probably no parent block with this name')
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
            return self.environment.undefined(name)
    else:
        def __missing__(self, key):
            return self.environment.undefined(key)

    def __repr__(self):
        return '<%s %s of %r>' % (
            self.__class__.__name__,
            dict.__repr__(self),
            self.filename
        )


class SuperBlock(object):
    """When called this renders a parent block."""

    def __init__(self, name, context, render_func):
        self.name = name
        self._context = context
        self._render_func = render_func

    def __call__(self):
        return TemplateData(u''.join(self._render_func(self._context)))

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
        self._filename = template.name
        self._rendered_body = u''.join(gen)
        self._context = context.get_exported()

    def __getitem__(self, name):
        return self._context[name]

    def __unicode__(self):
        return self._context

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self._filename
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
    revindex = property(lambda x: x.length)
    revindex0 = property(lambda x: x.length - 1)

    def __len__(self):
        return self.length


class LoopContext(LoopContextBase):
    """A loop context for dynamic iteration."""

    def __init__(self, iterable, parent=None, enforce_length=False):
        self._iterable = iterable
        self._next = iter(iterable).next
        self._length = None
        self.index0 = -1
        self.parent = parent
        if enforce_length:
            len(self)

    def make_static(self):
        """Return a static loop context for the optimizer."""
        parent = None
        if self.parent is not None:
            parent = self.parent.make_static()
        return StaticLoopContext(self.index0, self.length, parent)

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
    function call)."""

    def __init__(self, index0, length, parent):
        self.index0 = index0
        self.parent = parent
        self.length = length

    def __repr__(self):
        """The repr is used by the optimizer to dump the object."""
        return 'StaticLoopContext(%r, %r, %r)' % (
            self.index0,
            self.length,
            self.parent
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
                        value = self._environment.undefined(name,
                            extra='parameter not provided')
            arguments['l_' + name] = value
        if self.caller:
            caller = kwargs.pop('caller', None)
            if caller is None:
                caller = self._environment.undefined('caller',
                    extra='The macro was called from an expression and not '
                          'a call block.')
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

    def __init__(self, name=None, attr=None, extra=None):
        if attr is None:
            self._undefined_hint = '%r is undefined' % name
            self._error_class = NameError
        else:
            self._undefined_hint = '%r has no attribute named %r' \
                                   % (name, attr)
            self._error_class = AttributeError
        if extra is not None:
            self._undefined_hint += ' (' + extra + ')'

    def _fail_with_error(self, *args, **kwargs):
        raise self._error_class(self._undefined_hint)
    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
    __realdiv__ = __rrealdiv__ = __floordiv__ = __rfloordiv__ = \
    __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
    __getattr__ = __getitem__ = _fail_with_error

    def __unicode__(self):
        return u''

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __repr__(self):
        return 'undefined'

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
        return u'{{ %s }}' % self._undefined_hint


class StrictUndefined(Undefined):
    """An undefined that barks on print and iteration."""

    __iter__ = __unicode__ = __len__ = Undefined._fail_with_error
