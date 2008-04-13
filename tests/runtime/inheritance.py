from jinja2 import Environment, FileSystemLoader
e = Environment(loader=FileSystemLoader('templates'))

from jinja2.parser import Parser
from jinja2.translators.python import PythonTranslator

tmpl = e.loader.load('c.html')
print tmpl.render()
