from jinja2 import Environment
from jinja2.compiler import generate


env = Environment()
ast = env.parse("""
Hallo {{ name|e }}!, wie geht es {{ "<dir>"|e|lower }}?
""")
print ast
print
print generate(ast, env, "foo.html")
