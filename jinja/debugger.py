# -*- coding: utf-8 -*-
"""
    jinja.debugger
    ~~~~~~~~~~~~~~

    The debugger module of awesomeness.

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import sys
from random import randrange
from opcode import opmap
from types import CodeType

# if we have extended debugger support we should really use it
try:
    from jinja._debugger import *
    has_extended_debugger = True
except ImportError:
    has_extended_debugger = False

# we need the RUNTIME_EXCEPTION_OFFSET to skip the not used frames
from jinja.utils import RUNTIME_EXCEPTION_OFFSET


def fake_template_exception(exc_type, exc_value, traceback, filename, lineno,
                            source, context_or_env):
    """
    Raise an exception "in a template". Return a traceback
    object. This is used for runtime debugging, not compile time.
    """
    # some traceback systems allow to skip frames
    __traceback_hide__ = True

    # create the namespace which will be the local namespace
    # of the new frame then. Some debuggers show local variables
    # so we better inject the context and not the evaluation loop context.
    from jinja.datastructure import Context
    if isinstance(context_or_env, Context):
        env = context_or_env.environment
        namespace = context_or_env.to_dict()
    else:
        env = context_or_env
        namespace = {}

    # no unicode for filenames
    if isinstance(filename, unicode):
        filename = filename.encode('utf-8')

    # generate an jinja unique filename used so that linecache
    # gets data that doesn't interferes with other modules
    if filename is None:
        vfilename = 'jinja://~%d' % randrange(0, 10000)
        filename = '<string>'
    else:
        vfilename = 'jinja://%s' % filename

    # now create the used loaded and update the linecache
    loader = TracebackLoader(env, source, filename)
    loader.update_linecache(vfilename)
    globals = {
        '__name__':                 vfilename,
        '__file__':                 vfilename,
        '__loader__':               loader
    }

    # use the simple debugger to reraise the exception in the
    # line where the error originally occoured
    globals['__exception_to_raise__'] = (exc_type, exc_value)
    offset = '\n' * (lineno - 1)
    code = compile(offset + 'raise __exception_to_raise__[0], '
                            '__exception_to_raise__[1]',
                   vfilename or '<template>', 'exec')
    try:
        exec code in globals, namespace
    except:
        exc_info = sys.exc_info()

    # if we have an extended debugger we set the tb_next flag
    if has_extended_debugger and traceback is not None:
        tb_set_next(exc_info[2].tb_next, traceback.tb_next)

    # otherwise just return the exc_info from the simple debugger
    return exc_info


def translate_exception(template, context, exc_type, exc_value, traceback):
    """
    Translate an exception and return the new traceback.
    """
    # depending on the python version we have to skip some frames to
    # step to get the frame of the current template. The frames before
    # are the toolchain used to render that thing.
    for x in xrange(RUNTIME_EXCEPTION_OFFSET):
        traceback = traceback.tb_next

    # the next thing we do is matching the current error line against the
    # debugging table to get the correct source line. If we can't find the
    # filename and line number we return the traceback object unaltered.
    error_line = traceback.tb_lineno
    for code_line, tmpl_filename, tmpl_line in template._debug_info[::-1]:
        if code_line <= error_line:
            break
    else:
        return traceback

    return fake_template_exception(exc_type, exc_value, traceback,
                                   tmpl_filename, tmpl_line,
                                   template._source, context)


def raise_syntax_error(exception, env, source=None):
    """
    This method raises an exception that includes more debugging
    informations so that debugging works better. Unlike
    `translate_exception` this method raises the exception with
    the traceback.
    """
    exc_info = fake_template_exception(exception, None, None,
                                       exception.filename,
                                       exception.lineno, source, env)
    raise exc_info[0], exc_info[1], exc_info[2]


class TracebackLoader(object):
    """
    Fake importer that just returns the source of a template.
    """

    def __init__(self, environment, source, filename):
        self.loader = environment.loader
        self.source = source
        self.filename = filename

    def update_linecache(self, virtual_filename):
        """
        Hacky way to let traceback systems know about the
        Jinja template sourcecode. Very hackish indeed.
        """
        # check for linecache, not every implementation of python
        # might have such an module.
        try:
            from linecache import cache
        except ImportError:
            return
        data = self.get_source(None)
        cache[virtual_filename] = (
            len(data),
            None,
            data.splitlines(True),
            virtual_filename
        )

    def get_source(self, impname):
        source = ''
        if self.source is not None:
            source = self.source
        elif self.loader is not None:
            try:
                source = self.loader.get_source(self.filename)
            except TemplateNotFound:
                pass
        if isinstance(source, unicode):
            source = source.encode('utf-8')
        return source
