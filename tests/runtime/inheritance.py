from jinja import Environment, FileSystemLoader
e = Environment(loader=FileSystemLoader('templates'))

from jinja.parser import Parser
from jinja.translators.python import PythonTranslator

tmpl = e.loader.load('c.html')
print tmpl.render()
