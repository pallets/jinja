from jinja2 import Environment

print Environment().from_string("""\
{{ foo.bar }}
{% trans %}Hello {{ user }}!{% endtrans %}
{% trans count=users|count %}{{ count }} user{% pluralize %}{{ count }} users{% endtrans %}
""").render(user="someone")
