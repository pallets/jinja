from jinja2 import Environment
from jinja2.compiler import generate
from jinja2.optimizer import optimize


env = Environment()
forums = [
    {'id': 1, 'name': u'Example'},
    {'id': 2, 'name': u'Foobar'},
    {'id': 3, 'name': u'<42>'}
]
ast = env.parse("""
    Hi {{ "<blub>"|e }},
    how are you?

    {% for forum in forums %}
        {{ readstatus(forum.id) }} {{ forum.id|e }} {{ forum.name|e }}
    {% endfor %}

    {% navigation = [('#foo', 'Foo'), ('#bar', 'Bar')] %}
    <ul>
    {% for item in navigation %}
        <li><a href="{{ item[0] }}">{{ item[1] }}</a></li>
    {% endfor %}
    </ul>
""")
print ast
print
print generate(ast, env, "foo.html")
print
ast = optimize(ast, env, context_hint={'forums': forums})
print ast
print
print generate(ast, env, "foo.html")
