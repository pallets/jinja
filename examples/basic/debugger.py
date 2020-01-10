from __future__ import print_function

from jinja import Environment
from jinja.loaders import FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
tmpl = env.get_template("broken.html")
print(tmpl.render(seq=[3, 2, 4, 5, 3, 2, 0, 2, 1]))
