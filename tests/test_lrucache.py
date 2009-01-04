# -*- coding: utf-8 -*-
"""
    Tests the LRUCache
    ~~~~~~~~~~~~~~~~~~

    This module tests the LRU Cache

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD.
"""
import thread
import time
import random
import pickle
from jinja2.utils import LRUCache


def test_simple():
    d = LRUCache(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["a"]
    d["d"] = 4
    assert len(d) == 3
    assert 'a' in d and 'c' in d and 'd' in d and 'b' not in d


def test_pickleable():
    cache = LRUCache(2)
    cache["foo"] = 42
    cache["bar"] = 23
    cache["foo"]

    for protocol in range(3):
        copy = pickle.loads(pickle.dumps(cache, protocol))
        assert copy.capacity == cache.capacity
        assert copy._mapping == cache._mapping
        assert copy._queue == cache._queue
