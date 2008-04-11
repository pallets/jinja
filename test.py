import sys
from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
{% extends master_layout or "foo.html" %}

{% baz = [1, 2, 3, 4] %}
{% macro foo() %}
    blah
{% endmacro %}
{% blah = 42 %}

{% block body %}
    Das ist ein Test
{% endblock %}
""")
source = generate(ast, env, "foo.html")
print source
