# -*- coding: utf-8 -*-
"""
    jinja2.debug
    ~~~~~~~~~~~~

    Implements the debug interface for Jinja.  This module does some pretty
    ugly stuff with the Python traceback system in order to achieve tracebacks
    with correct line numbers, locals and contents.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import sys
from jinja2.utils import CodeType


def translate_exception(exc_info):
    """If passed an exc_info it will automatically rewrite the exceptions
    all the way down to the correct line numbers and frames.
    """
    result_tb = prev_tb = None
    initial_tb = tb = exc_info[2].tb_next

    while tb is not None:
        template = tb.tb_frame.f_globals.get('__jinja_template__')
        if template is not None:
            lineno = template.get_corresponding_lineno(tb.tb_lineno)
            tb = fake_exc_info(exc_info[:2] + (tb,), template.filename,
                               lineno, prev_tb)[2]
        if result_tb is None:
            result_tb = tb
        prev_tb = tb
        tb = tb.tb_next

    return exc_info[:2] + (result_tb or initial_tb,)


def fake_exc_info(exc_info, filename, lineno, tb_back=None):
    """Helper for `translate_exception`."""
    exc_type, exc_value, tb = exc_info

    # figure the real context out
    real_locals = tb.tb_frame.f_locals.copy()
    ctx = real_locals.get('context')
    if ctx:
        locals = ctx.get_all()
    else:
        locals = {}
    for name, value in real_locals.iteritems():
        if name.startswith('l_'):
            locals[name[2:]] = value

    # if there is a local called __jinja_exception__, we get
    # rid of it to not break the debug functionality.
    locals.pop('__jinja_exception__', None)

    # assamble fake globals we need
    globals = {
        '__name__':             filename,
        '__file__':             filename,
        '__jinja_exception__':  exc_info[:2]
    }

    # and fake the exception
    code = compile('\n' * (lineno - 1) + 'raise __jinja_exception__[0], ' +
                   '__jinja_exception__[1]', filename, 'exec')

    # if it's possible, change the name of the code.  This won't work
    # on some python environments such as google appengine
    try:
        function = tb.tb_frame.f_code.co_name
        if function == 'root':
            location = 'top-level template code'
        elif function.startswith('block_'):
            location = 'block "%s"' % function[6:]
        else:
            location = 'template'
        code = CodeType(0, code.co_nlocals, code.co_stacksize,
                        code.co_flags, code.co_code, code.co_consts,
                        code.co_names, code.co_varnames, filename,
                        location, code.co_firstlineno,
                        code.co_lnotab, (), ())
    except:
        pass

    # execute the code and catch the new traceback
    try:
        exec code in globals, locals
    except:
        exc_info = sys.exc_info()
        new_tb = exc_info[2].tb_next

    # now we can patch the exc info accordingly
    if tb_set_next is not None:
        if tb_back is not None:
            tb_set_next(tb_back, new_tb)
        if tb is not None:
            tb_set_next(new_tb, tb.tb_next)

    # return without this frame
    return exc_info[:2] + (new_tb,)


def _init_ugly_crap():
    """This function implements a few ugly things so that we can patch the
    traceback objects.  The function returned allows resetting `tb_next` on
    any python traceback object.
    """
    import ctypes
    from types import TracebackType

    # figure out side of _Py_ssize_t
    if hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
        _Py_ssize_t = ctypes.c_int64
    else:
        _Py_ssize_t = ctypes.c_int

    # regular python
    class _PyObject(ctypes.Structure):
        pass
    _PyObject._fields_ = [
        ('ob_refcnt', _Py_ssize_t),
        ('ob_type', ctypes.POINTER(_PyObject))
    ]

    # python with trace
    if object.__basicsize__ != ctypes.sizeof(_PyObject):
        class _PyObject(ctypes.Structure):
            pass
        _PyObject._fields_ = [
            ('_ob_next', ctypes.POINTER(_PyObject)),
            ('_ob_prev', ctypes.POINTER(_PyObject)),
            ('ob_refcnt', _Py_ssize_t),
            ('ob_type', ctypes.POINTER(_PyObject))
        ]

    class _Traceback(_PyObject):
        pass
    _Traceback._fields_ = [
        ('tb_next', ctypes.POINTER(_Traceback)),
        ('tb_frame', ctypes.POINTER(_PyObject)),
        ('tb_lasti', ctypes.c_int),
        ('tb_lineno', ctypes.c_int)
    ]

    def tb_set_next(tb, next):
        """Set the tb_next attribute of a traceback object."""
        if not (isinstance(tb, TracebackType) and
                (next is None or isinstance(next, TracebackType))):
            raise TypeError('tb_set_next arguments must be traceback objects')
        obj = _Traceback.from_address(id(tb))
        if tb.tb_next is not None:
            old = _Traceback.from_address(id(tb.tb_next))
            old.ob_refcnt -= 1
        if next is None:
            obj.tb_next = ctypes.POINTER(_Traceback)()
        else:
            next = _Traceback.from_address(id(next))
            next.ob_refcnt += 1
            obj.tb_next = ctypes.pointer(next)

    return tb_set_next


# try to get a tb_set_next implementation
try:
    from jinja2._speedups import tb_set_next
except ImportError:
    try:
        tb_set_next = _init_ugly_crap()
    except:
        tb_set_next = None
del _init_ugly_crap
