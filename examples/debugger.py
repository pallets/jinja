from jinja2 import Environment
from jinja2.loaders import FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

tmpl = env.get_template('broken.html')
print tmpl.render(seq=range(10))
