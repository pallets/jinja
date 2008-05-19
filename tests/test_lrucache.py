# -*- coding: utf-8 -*-
"""
    Tests the LRUCache
    ~~~~~~~~~~~~~~~~~~

    This module tests the LRU Cache

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: GNU GPL.
"""
import thread
import time
import random
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
