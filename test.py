import sys 
from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
{% block body %}
    {% b = 23 %}
    {% macro foo(a) %}[{{ a }}|{{ b }}|{{ c }}]{% endmacro %}
    {% for item in seq %}
      {{ foo(item) }}
    {%- endfor %}
{% endblock %}
""")
print ast
print
source = generate(ast, env, "foo.html")
print source
print

# execute the template
code = compile(source, 'jinja://foo.html', 'exec')
context = {'seq': range(5), 'c': 'foobar'}
namespace = {'global_context': context}
exec code in namespace
for event in namespace['root'](context):
    sys.stdout.write(event)
