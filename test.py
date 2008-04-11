from jinja2 import Environment
from jinja2.loaders import DictLoader

env = Environment(loader=DictLoader({
'child.html': u'''\
{% extends master_layout or 'master.html' %}
{% include 'helpers.html' %}
{% macro get_the_answer() %}42{% endmacro %}
{% block body %}
    {{ get_the_answer() }}
    {{ conspirate() }}
{% endblock %}
''',
'master.html': u'''\
<!doctype html>
<title>Foo</title>
{% block body %}{% endblock %}
''',
'helpers.html': u'''\
{% macro conspirate() %}23{% endmacro %}
'''
}))


tmpl = env.get_template("child.html")
print tmpl.render()
