from jinja2 import Environment

env = Environment()
tmpl = env.from_string("""
<ul>
{% for item in seq %}
    <li>{{ item|e }}</li>
{% endfor %}
</ul>
""")

print tmpl.render(seq=range(10))
