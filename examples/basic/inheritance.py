from __future__ import print_function

from jinja import Environment
from jinja.loaders import DictLoader

env = Environment(
    loader=DictLoader(
        {
            "a": "[A[{% block body %}{% endblock %}]]",
            "b": "{% extends 'a' %}{% block body %}[B]{% endblock %}",
            "c": "{% extends 'b' %}{% block body %}###{{ super() }}###{% endblock %}",
        }
    )
)
print(env.get_template("c").render())
