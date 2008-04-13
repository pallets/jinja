from django.conf import settings
settings.configure()
from django.template import Template as DjangoTemplate, Context as DjangoContext
from jinja2 import Environment as JinjaEnvironment
from mako.template import Template as MakoTemplate
from timeit import Timer


jinja_template = JinjaEnvironment(
    line_statement_prefix='%',
    variable_start_string="${",
    variable_end_string="}"
).from_string("""\
<!doctype html>
<html>
  <head>
    <title>${page_title|e}
  </head>
  <body>
    <div class="header">
      <h1>${page_title|e}</h1>
    </div>
    <ul class="navigation">
    % for href, caption in [
        ('index.html', 'Index'),
        ('downloads.html', 'Downloads'),
        ('products.html', 'Products')
      ]
      <li><a href="${href|e}">${caption|e}</a></li>
    % endfor
    </ul>
    <div class="table">
      <table>
      % for row in table
        <tr>
        % for cell in row
          <td>${cell}</td>
        % endfor
        </tr>
      % endfor
      </table>
    </div>
  </body>
</html>\
""")

django_template = DjangoTemplate("""\
<!doctype html>
<html>
  <head>
    <title>{{ page_title }}
  </head>
  <body>
    <div class="header">
      <h1>{{ page_title }}</h1>
    </div>
    <ul class="navigation">
    {% for href, caption in navigation %}
      <li><a href="{{ href }}">{{ caption }}</a></li>
    {% endfor %}
    </ul>
    <div class="table">
      <table>
      {% for row in table %}
        <tr>
        {% for cell in row %}
          <td>{{ cell }}</td>
        {% endfor %}
        </tr>
      {% endfor %}
      </table>
    </div>
  </body>
</html>\
""")

mako_template = MakoTemplate("""\
<!doctype html>
<html>
  <head>
    <title>${page_title|h}
  </head>
  <body>
    <div class="header">
      <h1>${page_title|h}</h1>
    </div>
    <ul class="navigation">
    % for href, caption in [('index.html', 'Index'), ('downloads.html', 'Downloads'), ('products.html', 'Products')]:
      <li><a href="${href|h}">${caption|h}</a></li>
    % endfor
    </ul>
    <div class="table">
      <table>
      % for row in table:
        <tr>
        % for cell in row:
          <td>${cell}</td>
        % endfor
        </tr>
      % endfor
      </table>
    </div>
  </body>
</html>\
""")

context = {
    'page_title': 'mitsuhiko\'s benchmark',
    'table': [dict(a=1,b=2,c=3,d=4,e=5,f=6,g=7,h=8,i=9,j=10) for x in range(1000)]
}

def test_jinja():
    jinja_template.render(context)

def test_django():
    c = DjangoContext(context)
    c['navigation'] = [('index.html', 'Index'), ('downloads.html', 'Downloads'), ('products.html', 'Products')]
    django_template.render(c)

def test_mako():
    mako_template.render(**context)


for test in 'jinja', 'mako', 'django':
    t = Timer(setup='from __main__ import test_%s as bench' % test,
              stmt='bench()')
    print '%-20s%.4fms' % (test, t.timeit(number=20) / 20)
