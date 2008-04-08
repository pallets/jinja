from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
{% block body %}
    {% b = 23 %}
    {% macro foo(a) %}[{{ a }}|{{ b }}|{{ c }}]{% endmacro %}
    {% for item in seq %}
      {{ foo(item) }}
    {% endfor %}
{% endblock %}
""")
print ast
print
print generate(ast, "foo.html")
