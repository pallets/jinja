from jinja2 import Environment
from jinja2.loaders import DictLoader

env = Environment(loader=DictLoader({
'child.html': u'''\
{% extends master_layout or 'master.html' %}
{% macro get_the_answer() %}42{% endmacro %}
{% block body %}
    {{ get_the_answer() }}
{% endblock %}
''',
'master.html': u'''\
<!doctype html>
<title>Foo</title>
{% block body %}{% endblock %}
'''
}))


tmpl = env.get_template("child.html")
print tmpl.render()
