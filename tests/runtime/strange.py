import jdebug
from jinja2 import Environment, DictLoader

base_tmpl = """
{% block content %}Default{% endblock %}
"""

### condition is inside of block

test1 = """
{% extends 'base' %}

{% block content %}
  {% if False %}
    {{ throw_exception() }}
  {% endif %}
{% endblock %}
"""

### block is inside of condition

test2 = """
{% extends 'base' %}

{% if False %}
  {% block content %}
    {{ throw_exception() }}
  {% endblock %}
{% endif %}
"""

class TestException(Exception):
    pass

def throw_exception():
    raise TestException()

env = Environment(
    loader=DictLoader(dict(base=base_tmpl))
)

if __name__ == '__main__':
    for name in 'test1', 'test2':
        template_body = globals().get(name)
        template = env.from_string(template_body)
        try:
            print 'Rendering template:\n"""%s"""' % template_body
            template.render(throw_exception=throw_exception)
        except TestException:
            print 'Result: throw_exception() was called'
        else:
            print 'Result: throw_exception() was not called'
        print

    print 'First template illustrates that condition is working well'
    print 'The question is - why {% block %} is being evalueted '\
          'in false condition in second template?'
