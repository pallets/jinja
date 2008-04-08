from jinja2 import Environment
from jinja2.compiler import generate
from jinja2.optimizer import optimize


env = Environment()
ast = env.parse("""
    Hi {{ "<blub>"|e }},
    how are you?
""")
print ast
print
print generate(ast, env, "foo.html")
print
ast = optimize(ast, env)
print ast
print
print generate(ast, env, "foo.html")
