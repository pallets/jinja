# test file for block super support
import jdebug
from jinja import Environment, DictLoader

env = Environment(loader=DictLoader({
    'a': '''\
<title>{{ title|e }}</title>
<body>
    {% block body %}Default{% endblock %}
</body>
''',
    'b': '''
{% set foo = 42 %}
''',
    'c': '''
{% extends 'a' %}
{% if true %}
    {% set title = "foo" %}
{% endif %}
{% include 'b' %}
{% include 'tools' %}
{% block body %}
    hehe, this comes from b: {{ foo }}

    Say hello to the former block content:
        {{ say_hello(super()) }}
{% endblock %}
''',
    'tools': '''
{% macro say_hello name -%}
    Hello {{ name }}!
{%- endmacro %}
'''
}))

tmpl = env.get_template('c')
print tmpl.render()
