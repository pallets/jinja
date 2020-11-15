import pytest

from jinja2 import Environment

class TestTatsuLexer:
    def test_simple(self, env):
        env = Environment(tatsu_lexer=True)
        tmpl = env.from_string(
            "<p>simple test</p>"
            "{% if kvs %}"
            "  {% for k, v in kvs %}{{ k }}={{ v }} {% endfor %}"
            "{% endif %}"
        )
        assert tmpl.render(kvs=[("a", 1), ("b", 2)]) == "<p>simple test</p>  a=1 b=2 "