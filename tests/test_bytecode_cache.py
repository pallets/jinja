# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.bytecode_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test bytecode caching

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import pytest
from jinja2 import Environment
from jinja2.bccache import FileSystemBytecodeCache, MemcachedBytecodeCache,\
    Bucket
from jinja2.exceptions import TemplateNotFound


@pytest.fixture
def env(package_loader):
    bytecode_cache = FileSystemBytecodeCache()
    return Environment(
        loader=package_loader,
        bytecode_cache=bytecode_cache,
    )


@pytest.mark.byte_code_cache
class TestByteCodeCache(object):

    def test_simple(self, env):
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        pytest.raises(TemplateNotFound, env.get_template, 'missing.html')


class MockMemcached(object):

    def get(self, key):
        return "value"

    def set(self, *args):
        pass

    def get_side_effect(self, key):
        raise Exception()

    def set_side_effect(self, *args):
        raise Exception()


class TestMemcachedBytecodeCache(object):

    def test_load_bytecode(self):

        # Python 2.X does not have explicit bytes type and Python 3.X's
        # str type does not support Buffer interface
        try:
            key = bytes("key", "utf-8")  # PY 3.X
        except:
            key = "key"  # PY 2.X

        m = MemcachedBytecodeCache(MockMemcached())
        b = Bucket("", key, "")
        m.load_bytecode(b)

    def test_load_bytecode_exception(self):
        memcached = MockMemcached()
        memcached.get = memcached.get_side_effect
        m = MemcachedBytecodeCache(memcached)
        b = Bucket("", "key", "")
        m.load_bytecode(b)

    def test_load_bytecode_exception_raise(self):
        memcached = MockMemcached()
        memcached.get = memcached.get_side_effect
        m = MemcachedBytecodeCache(memcached, ignore_memcache_errors=False)
        b = Bucket("", "key", "")
        with pytest.raises(Exception):
            m.load_bytecode(b)

    def test_dump_bytecode(self):
        memcached = MockMemcached()
        m = MemcachedBytecodeCache(memcached, timeout=10)
        b = Bucket("", "key", "")
        b.code = "code"
        m.dump_bytecode(b)

    def test_dump_bytecode_exception_raise(self):
        memcached = MockMemcached()
        memcached.set = memcached.set_side_effect
        m = MemcachedBytecodeCache(memcached, ignore_memcache_errors=False)
        b = Bucket("", "key", "")
        b.code = "code"
        with pytest.raises(Exception):
            m.dump_bytecode(b)
