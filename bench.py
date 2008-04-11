from jinja import Environment as E1
from jinja2 import Environment as E2
from mako.template import Template as M

t1, t2 = [e.from_string("""
<ul>
{%- for item in seq %}
    <li>{{ item|e }}</li>
{%- endfor %}
</ul>
""") for e in E1(), E2()]

m = M("""
<ul>
% for item in seq:
    <li>${item|h}</li>
% endfor
</ul>
""")
