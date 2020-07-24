from jinja2 import Environment
from jinja2.loaders import DictLoader

env = Environment(
    loader=DictLoader(
        {
            "child.html": """\
{% extends master_layout or 'master.html' %}
{% include helpers = 'helpers.html' %}
{% macro get_the_answer() %}42{% endmacro %}
{% title = 'Hello World' %}
{% block body %}
    {{ get_the_answer() }}
    {{ helpers.conspirate() }}
{% endblock %}
""",
            "master.html": """\
<!doctype html>
<title>{{ title }}</title>
{% block body %}{% endblock %}
""",
            "helpers.html": """\
{% macro conspirate() %}23{% endmacro %}
""",
        }
    )
)
tmpl = env.get_template("child.html")
print(tmpl.render())
