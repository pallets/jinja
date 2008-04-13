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


__all__ = ['subscribe', 'LoopContext', 'StaticLoopContext', 'TemplateContext',
           'Macro', 'IncludedTemplate', 'Undefined', 'TemplateData']


def subscribe(obj, argument):
    """Get an item or attribute of an object."""
    try:
        return getattr(obj, str(argument))
    except (AttributeError, UnicodeError):
        try:
            return obj[argument]
        except (TypeError, LookupError):
            return Undefined(obj, argument)


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

    def __init__(self, globals, filename, blocks, standalone):
        dict.__init__(self, globals)
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

    def __setitem__(self, key, value):
        """If we set items to the dict we track the variables set so
        that includes can access the exported variables."""
        dict.__setitem__(self, key, value)
        self.exported.add(key)

    def __delitem__(self, key):
        """On delete we no longer export it."""
        dict.__delitem__(self, key)
        self.exported.dicard(key)

    def get_exported(self):
        """Get a dict of all exported variables."""
        return dict((k, self[k]) for k in self.exported)

    # if there is a default dict, dict has a __missing__ method we can use.
    if defaultdict is None:
        def __getitem__(self, name):
            if name in self:
                return self[name]
            return Undefined(name)
    else:
        def __missing__(self, key):
            return Undefined(key)

    def __repr__(self):
        return '<%s %s of %r>' % (
            self.__class__.__name__,
            dict.__repr__(self),
            self.filename
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

    first = property(lambda x: x.index0 == 0)
    last = property(lambda x: x.revindex0 == 0)
    index = property(lambda x: x.index0 + 1)
    revindex = property(lambda x: x.length)
    revindex0 = property(lambda x: x.length - 1)
    length = property(lambda x: len(x))


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

    def __len__(self):
        if self._length is None:
            try:
                length = len(self._iterable)
            except TypeError:
                self._iterable = tuple(self._iterable)
                self._next = iter(self._iterable).next
                length = len(tuple(self._iterable)) + self.index0 + 1
            self._length = length
        return self._length


class StaticLoopContext(LoopContextBase):
    """The static loop context is used in the optimizer to "freeze" the
    status of an iteration.  The only reason for this object is if the
    loop object is accessed in a non static way (eg: becomes part of a
    function call)."""

    def __init__(self, index0, length, parent):
        self.index0 = index0
        self.parent = parent
        self._length = length

    def __repr__(self):
        """The repr is used by the optimizer to dump the object."""
        return 'StaticLoopContext(%r, %r, %r)' % (
            self.index0,
            self._length,
            self.parent
        )

    def __len__(self):
        return self._length

    def make_static(self):
        return self


class Macro(object):
    """Wraps a macro."""

    def __init__(self, func, name, arguments, defaults, catch_all, caller):
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
                        value = Undefined(name, extra='parameter not provided')
            arguments['l_' + name] = value
        if self.caller:
            caller = kwargs.pop('caller', None)
            if caller is None:
                caller = Undefined('caller', extra='The macro was called '
                                   'from an expression and not a call block.')
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
    """The object for undefined values."""

    def __init__(self, name=None, attr=None, extra=None):
        if attr is None:
            self._undefined_hint = '%r is undefined' % name
        else:
            self._undefined_hint = 'attribute %r of %r is undefined' \
                                   % (attr, name)
        if extra is not None:
            self._undefined_hint += ' (' + extra + ')'

    def fail(self, *args, **kwargs):
        raise TypeError(self._undefined_hint)
    __getattr__ = __getitem__ = __add__ = __mul__ = __div__ = \
    __realdiv__ = __floordiv__ = __mod__ = __pos__ = __neg__ = \
    __call__ = fail
    del fail

    def __unicode__(self):
        return ''

    def __repr__(self):
        return 'Undefined'

    def __len__(self):
        return 0

    def __iter__(self):
        if 0:
            yield None
