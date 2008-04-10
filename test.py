import sys 
from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
hallo
{% block root %}
  inhalt
  {% x = 3 %}
  {% block inner %}
    {% x = x + 2 %}
    {{ x }}
  {% endblock %}
  {{ x }}
{% endblock %}
ende
""")
source = generate(ast, env, "foo.html")
print source
