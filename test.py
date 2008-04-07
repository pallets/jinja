from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
Hello {{ name }}!.  How is it {{ "going" }}. {{ [1, 2, 3] }}?
{% for name in user_names %}
    {{ loop.index }}: {{ name }}
    {% if loop.index % 2 == 0 %}...{% endif %}
{% endfor %}
Name again: {{ name }}!
""")
print ast
print
print generate(ast, "foo.html")
