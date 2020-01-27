# -*- coding: utf-8 -*-
import pickle
import random
from collections import deque
from copy import copy as shallow_copy

import pytest
from markupsafe import Markup

from jinja2._compat import range_type
from jinja2._compat import string_types
from jinja2.utils import consume
from jinja2.utils import generate_lorem_ipsum
from jinja2.utils import LRUCache
from jinja2.utils import missing
from jinja2.utils import object_type_repr
from jinja2.utils import select_autoescape
from jinja2.utils import urlize


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
        assert "a" in d and "c" in d and "d" in d and "b" not in d

    def test_itervalues(self):
        cache = LRUCache(3)
        cache["b"] = 1
        cache["a"] = 2
        values = [v for v in cache.values()]
        assert len(values) == 2
        assert 1 in values
        assert 2 in values

    def test_itervalues_empty(self):
        cache = LRUCache(2)
        values = [v for v in cache.values()]
        assert len(values) == 0

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

    @pytest.mark.parametrize("copy_func", [LRUCache.copy, shallow_copy])
    def test_copy(self, copy_func):
        cache = LRUCache(2)
        cache["a"] = 1
        cache["b"] = 2
        copy = copy_func(cache)
        assert copy._queue == cache._queue
        copy["c"] = 3
        assert copy._queue != cache._queue
        assert "a" not in copy and "b" in copy and "c" in copy

    def test_clear(self):
        d = LRUCache(3)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        d.clear()
        assert d.__getstate__() == {"capacity": 3, "_mapping": {}, "_queue": deque([])}

    def test_repr(self):
        d = LRUCache(3)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        # Sort the strings - mapping is unordered
        assert sorted(repr(d)) == sorted(u"<LRUCache {'a': 1, 'b': 2, 'c': 3}>")

    def test_items(self):
        """Test various items, keys, values and iterators of LRUCache."""
        d = LRUCache(3)
        d["a"] = 1
        d["b"] = 2
        d["c"] = 3
        assert d.items() == [("c", 3), ("b", 2), ("a", 1)]
        assert d.keys() == ["c", "b", "a"]
        assert d.values() == [3, 2, 1]
        assert list(reversed(d)) == ["a", "b", "c"]

        # Change the cache a little
        d["b"]
        d["a"] = 4
        assert d.items() == [("a", 4), ("b", 2), ("c", 3)]
        assert d.keys() == ["a", "b", "c"]
        assert d.values() == [4, 2, 3]
        assert list(reversed(d)) == ["c", "b", "a"]

    def test_setdefault(self):
        d = LRUCache(3)
        assert len(d) == 0
        assert d.setdefault("a") is None
        assert d.setdefault("a", 1) is None
        assert len(d) == 1
        assert d.setdefault("b", 2) == 2
        assert len(d) == 2


@pytest.mark.utils
@pytest.mark.helpers
class TestHelpers(object):
    def test_object_type_repr(self):
        class X(object):
            pass

        assert object_type_repr(42) == "int object"
        assert object_type_repr([]) == "list object"
        assert object_type_repr(X()) == "test_utils.X object"
        assert object_type_repr(None) == "None"
        assert object_type_repr(Ellipsis) == "Ellipsis"

    def test_autoescape_select(self):
        func = select_autoescape(
            enabled_extensions=("html", ".htm"),
            disabled_extensions=("txt",),
            default_for_string="STRING",
            default="NONE",
        )

        assert func(None) == "STRING"
        assert func("unknown.foo") == "NONE"
        assert func("foo.html")
        assert func("foo.htm")
        assert not func("foo.txt")
        assert func("FOO.HTML")
        assert not func("FOO.TXT")


@pytest.mark.utils
@pytest.mark.escapeUrlizeTarget
class TestEscapeUrlizeTarget(object):
    def test_escape_urlize_target(self):
        url = "http://example.org"
        target = "<script>"
        assert urlize(url, target=target) == (
            '<a href="http://example.org"'
            ' target="&lt;script&gt;">'
            "http://example.org</a>"
        )


@pytest.mark.utils
@pytest.mark.loremIpsum
class TestLoremIpsum(object):
    def test_lorem_ipsum_markup(self):
        """Test that output of lorem_ipsum is Markup by default."""
        assert isinstance(generate_lorem_ipsum(), Markup)

    def test_lorem_ipsum_html(self):
        """Test that output of lorem_ipsum is a string_type when not html."""
        assert isinstance(generate_lorem_ipsum(html=False), string_types)

    def test_lorem_ipsum_n(self):
        """Test that the n (number of lines) works as expected."""
        assert generate_lorem_ipsum(n=0, html=False) == u""
        for n in range_type(1, 50):
            assert generate_lorem_ipsum(n=n, html=False).count("\n") == (n - 1) * 2

    def test_lorem_ipsum_min(self):
        """Test that at least min words are in the output of each line"""
        for _ in range_type(5):
            m = random.randrange(20, 99)
            for _ in range_type(10):
                assert generate_lorem_ipsum(n=1, min=m, html=False).count(" ") >= m - 1

    def test_lorem_ipsum_max(self):
        """Test that at least max words are in the output of each line"""
        for _ in range_type(5):
            m = random.randrange(21, 100)
            for _ in range_type(10):
                assert generate_lorem_ipsum(n=1, max=m, html=False).count(" ") < m - 1


def test_missing():
    """Test the repr of missing."""
    assert repr(missing) == u"missing"


def test_consume():
    """Test that consume consumes an iterator."""
    x = iter([1, 2, 3, 4, 5])
    consume(x)
    with pytest.raises(StopIteration):
        next(x)
