from jinja2 import Environment

env = Environment()
tmpl = env.from_string("""<!doctype html>
<html>
  <head>
    <title>{{ page_title|e }}</title>
  </head>
  <body>
    <ul class="navigation">
    {%- for href, caption in [
        ('index.html', 'Index'),
        ('projects.html', 'Projects'),
        ('about.html', 'About')
    ] %}
      <li><a href="{{ href|e }}">{{ caption|e }}</a></li>
    {%- endfor %}
    </ul>
    <div class="body">
      {{ body }}
    </div>
  </body>
</html>\
""")


print tmpl.render(page_title='<foo>', body='<p>Hello World</p>')
