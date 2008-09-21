# -*- coding: utf-8 -*-
"""
    Tests for old bugs
    ~~~~~~~~~~~~~~~~~~

    Unittest that test situations caused by various older bugs.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from jinja2 import Environment

def test_keyword_folding():
    env = Environment()
    env.filters['testing'] = lambda value, some: value + some
    assert env.from_string("{{ 'test'|testing(some='stuff') }}") \
           .render() == 'teststuff'

