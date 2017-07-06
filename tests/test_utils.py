# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.utils
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests utilities jinja uses.

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import gc

import pytest

import pickle

from jinja2.utils import LRUCache, escape, object_type_repr, urlize, \
     select_autoescape


@pytest.mark.utils
@pytest.mark.lrucache
class TestLRUCache(object):

    def test_simple(self):
        d = LRUCache(3)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        d["a"]
        d["d"] = 4
        assert len(d) == 3
        assert 'a' in d and 'c' in d and 'd' in d and 'b' not in d

    def test_pickleable(self):
        cache = LRUCache(2)
        cache["foo"] = 42
        cache["bar"] = 23
        cache["foo"]

        for protocol in range(3):
            copy = pickle.loads(pickle.dumps(cache, protocol))
            assert copy.capacity == cache.capacity
            assert copy._mapping == cache._mapping
            assert copy._queue == cache._queue


@pytest.mark.utils
@pytest.mark.helpers
class TestHelpers(object):

    def test_object_type_repr(self):
        class X(object):
            pass
        assert object_type_repr(42) == 'int object'
        assert object_type_repr([]) == 'list object'
        assert object_type_repr(X()) == 'test_utils.X object'
        assert object_type_repr(None) == 'None'
        assert object_type_repr(Ellipsis) == 'Ellipsis'

    def test_autoescape_select(self):
        func = select_autoescape(
            enabled_extensions=('html', '.htm'),
            disabled_extensions=('txt',),
            default_for_string='STRING',
            default='NONE',
        )

        assert func(None) == 'STRING'
        assert func('unknown.foo') == 'NONE'
        assert func('foo.html') == True
        assert func('foo.htm') == True
        assert func('foo.txt') == False
        assert func('FOO.HTML') == True
        assert func('FOO.TXT') == False


@pytest.mark.utils
@pytest.mark.escapeUrlizeTarget
class TestEscapeUrlizeTarget(object):
    def test_escape_urlize_target(self):
        url = "http://example.org"
        target = "<script>"
        assert urlize(url, target=target) == ('<a href="http://example.org"'
                                              ' target="&lt;script&gt;">'
                                              'http://example.org</a>')
