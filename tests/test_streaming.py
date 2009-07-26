# -*- coding: utf-8 -*-
"""
    unit test for streaming interface
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""

from jinja2 import Environment
env = Environment()


def test_basic_streaming():
    r"""
>>> tmpl = env.from_string("<ul>{% for item in seq %}<li>{{ loop.index "
...                        "}} - {{ item }}</li>{%- endfor %}</ul>")
>>> stream = tmpl.stream(seq=range(4))
>>> stream.next()
u'<ul>'
>>> stream.next()
u'<li>1 - 0</li>'
>>> stream.next()
u'<li>2 - 1</li>'
>>> stream.next()
u'<li>3 - 2</li>'
>>> stream.next()
u'<li>4 - 3</li>'
>>> stream.next()
u'</ul>'
"""

def test_buffered_streaming():
    r"""
>>> tmpl = env.from_string("<ul>{% for item in seq %}<li>{{ loop.index "
...                        "}} - {{ item }}</li>{%- endfor %}</ul>")
>>> stream = tmpl.stream(seq=range(4))
>>> stream.enable_buffering(size=3)
>>> stream.next()
u'<ul><li>1 - 0</li><li>2 - 1</li>'
>>> stream.next()
u'<li>3 - 2</li><li>4 - 3</li></ul>'
"""

def test_streaming_behavior():
    r"""
>>> tmpl = env.from_string("")
>>> stream = tmpl.stream()
>>> stream.buffered
False
>>> stream.enable_buffering(20)
>>> stream.buffered
True
>>> stream.disable_buffering()
>>> stream.buffered
False
"""
