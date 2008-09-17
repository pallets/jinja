# -*- coding: utf-8 -*-
"""
    jinja2.bccache
    ~~~~~~~~~~~~~~

    This module implements the bytecode cache system Jinja is optionally
    using.  This is useful if you have very complex template situations and
    the compiliation of all those templates slow down your application too
    much.

    Situations where this is useful are often forking web applications that
    are initialized on the first request.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from os import path
import marshal
import cPickle as pickle
from cStringIO import StringIO
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1


bc_version = 1
bc_magic = 'j2' + pickle.dumps(bc_version, 2)


class Bucket(object):
    """Buckets are used to store the bytecode for one template.  It's
    initialized by the bytecode cache with the checksum for the code
    as well as the unique key.

    The bucket then provides method to load the bytecode from file(-like)
    objects and strings or dump it again.
    """

    def __init__(self, cache, environment, key, checksum):
        self._cache = cache
        self.environment = environment
        self.key = key
        self.checksum = checksum
        self.reset()

    def reset(self):
        """Resets the bucket (unloads the code)."""
        self.code = None

    def load(self, f):
        """Loads bytecode from a f."""
        # make sure the magic header is correct
        magic = f.read(len(bc_magic))
        if magic != bc_magic:
            self.reset()
            return
        # the source code of the file changed, we need to reload
        checksum = pickle.load(f)
        if self.checksum != checksum:
            self.reset()
            return
        # now load the code.  Because marshal is not able to load
        # from arbitrary streams we have to work around that
        if isinstance(f, file):
            self.code = marshal.load(f)
        else:
            self.code = marshal.loads(f.read())

    def dump(self, f):
        """Dump the bytecode into f."""
        if self.code is None:
            raise TypeError('can\'t write empty bucket')
        f.write(bc_magic)
        pickle.dump(self.checksum, f, 2)
        if isinstance(f, file):
            marshal.dump(self.code, f)
        else:
            f.write(marshal.dumps(self.code))

    def loads(self, string):
        """Load bytecode from a string."""
        self.load(StringIO(string))

    def dumps(self):
        """Return the bytecode as string."""
        out = StringIO()
        self.dump(out)
        return out.getvalue()

    def write_back(self):
        """Write the bucket back to the cache."""
        self._cache.dump_bucket(self)


class BytecodeCache(object):
    """To implement your own bytecode cache you have to subclass this class
    and override :meth:`load_bucket` and :meth:`dump_bucket`.  Both of these
    methods are passed a :class:`Bucket` that they have to load or dump.
    """

    def load_bucket(self, bucket):
        """Subclasses have to override this method to load bytecode
        into a bucket.
        """
        raise NotImplementedError()

    def dump_bucket(self, bucket):
        """Subclasses have to override this method to write the
        bytecode from a bucket back to the cache.
        """
        raise NotImplementedError()

    def get_cache_key(self, name):
        """Return the unique hash key for this template name."""
        return sha1(name.encode('utf-8')).hexdigest()

    def get_source_checksum(self, source):
        """Return a checksum for the source."""
        return sha1(source.encode('utf-8')).hexdigest()

    def get_bucket(self, environment, name, source):
        """Return a cache bucket."""
        key = self.get_cache_key(name)
        checksum = self.get_source_checksum(source)
        bucket = Bucket(self, environment, key, checksum)
        self.load_bucket(bucket)
        return bucket


class FileSystemCache(BytecodeCache):
    """A bytecode cache that stores bytecode on the filesystem."""

    def __init__(self, directory, pattern='%s.jbc'):
        self.directory = directory
        self.pattern = pattern

    def _get_cache_filename(self, bucket):
        return path.join(self.directory, self.pattern % bucket.key)

    def load_bucket(self, bucket):
        filename = self._get_cache_filename(bucket)
        if path.exists(filename):
            f = file(filename, 'rb')
            try:
                bucket.load(f)
            finally:
                f.close()

    def dump_bucket(self, bucket):
        filename = self._get_cache_filename(bucket)
        f = file(filename, 'wb')
        try:
            bucket.dump(f)
        finally:
            f.close()
