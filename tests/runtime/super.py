# test file for block super support
import jdebug
from jinja2 import Environment, DictLoader

env = Environment(loader=DictLoader({
    'a': '{% block intro %}INTRO{% endblock %}|BEFORE|{% block data %}INNER{% endblock %}|AFTER',
    'b': '{% extends "a" %}{% block data %}({{ super() }}){% endblock %}',
    'c': '{% extends "b" %}{% block intro %}--{{ super() }}--{% endblock %}\n{% block data %}[{{ super() }}]{% endblock %}'
}))

tmpl = env.get_template('c')
print tmpl.render()
