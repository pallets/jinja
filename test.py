from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
{% (a, b), c = foo() %}
{% macro foo(a, b, c=42) %}
  42 {{ arguments }}
{% endmacro %}
{% block body %}
    {% bar = 23 %}
{% endblock %}
""")
print ast
print
print generate(ast, env, "foo.html")
