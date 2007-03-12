from jinja import Environment, FileSystemLoader
from colubrid.debug import DebuggedApplication
from wsgiref.simple_server import make_server
e = Environment(loader=FileSystemLoader('templates'))

def test(*args):
    tmpl = e.loader.load('error.html')
    tmpl.render(items=range(10))

make_server("localhost", 7000, DebuggedApplication(test, False)).serve_forever()
