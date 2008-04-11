from jinja import Environment as E1
from jinja2 import Environment as E2

t1, t2 = [e.from_string("""
<ul>
{%- for item in seq %}
    <li>{{ item|e }}</li>
{%- endfor %}
</ul>
""") for e in E1(), E2()]
