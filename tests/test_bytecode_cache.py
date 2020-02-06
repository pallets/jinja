# -*- coding: utf-8 -*-
import pytest

from jinja2 import Environment
from jinja2.bccache import Bucket
from jinja2.bccache import FileSystemBytecodeCache
from jinja2.bccache import MemcachedBytecodeCache
from jinja2.exceptions import TemplateNotFound


@pytest.fixture
def env(package_loader, tmp_path):
    bytecode_cache = FileSystemBytecodeCache(str(tmp_path))
    return Environment(loader=package_loader, bytecode_cache=bytecode_cache)


class TestByteCodeCache(object):
    def test_simple(self, env):
        tmpl = env.get_template("test.html")
        assert tmpl.render().strip() == "BAR"
        pytest.raises(TemplateNotFound, env.get_template, "missing.html")


class MockMemcached(object):
    class Error(Exception):
        pass

    key = None
    value = None
    timeout = None

    def get(self, key):
        return self.value

    def set(self, key, value, timeout=None):
        self.key = key
        self.value = value
        self.timeout = timeout

    def get_side_effect(self, key):
        raise self.Error()

    def set_side_effect(self, *args):
        raise self.Error()


class TestMemcachedBytecodeCache(object):
    def test_dump_load(self):
        memcached = MockMemcached()
        m = MemcachedBytecodeCache(memcached)

        b = Bucket(None, "key", "")
        b.code = "code"
        m.dump_bytecode(b)
        assert memcached.key == "jinja2/bytecode/key"

        b = Bucket(None, "key", "")
        m.load_bytecode(b)
        assert b.code == "code"

    def test_exception(self):
        memcached = MockMemcached()
        memcached.get = memcached.get_side_effect
        memcached.set = memcached.set_side_effect
        m = MemcachedBytecodeCache(memcached)
        b = Bucket(None, "key", "")
        b.code = "code"

        m.dump_bytecode(b)
        m.load_bytecode(b)

        m.ignore_memcache_errors = False

        with pytest.raises(MockMemcached.Error):
            m.dump_bytecode(b)

        with pytest.raises(MockMemcached.Error):
            m.load_bytecode(b)
