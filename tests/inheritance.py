from jinja import Environment, FileSystemLoader
e = Environment(loader=FileSystemLoader('templates'))

from jinja.parser import Parser
from jinja.translators.python import PythonTranslator

print PythonTranslator(e, e.loader.parse('index.html')).translate()
