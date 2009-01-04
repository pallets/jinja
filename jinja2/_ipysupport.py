# -*- coding: utf-8 -*-
"""
    jinja2._ipysupport
    ~~~~~~~~~~~~~~~~~~

    IronPython support library.  This library exports functionality from
    the CLR to Python that is normally available in the standard library.

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD.
"""
from System import DateTime
from System.IO import Path, File, FileInfo


epoch = DateTime(1970, 1, 1)


class _PathModule(object):
    """A minimal path module."""

    sep = str(Path.DirectorySeparatorChar)
    altsep = str(Path.AltDirectorySeparatorChar)
    pardir = '..'

    def join(self, path, *args):
        args = list(args[::-1])
        while args:
            path = Path.Combine(path, args.pop())
        return path

    def isfile(self, filename):
        return File.Exists(filename)

    def getmtime(self, filename):
        info = FileInfo(filename)
        return int((info.LastAccessTimeUtc - epoch).TotalSeconds)


path = _PathModule()
