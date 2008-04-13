import jdebug
from time import time
from jinja2 import Environment
tmpl = Environment().from_string('''
<h1>Bigtable</h1>
<table>
{%- for row in table -%}
  <tr>
  {%- for col in row.values() %}
    <td>{{ col }}</td>
  {%- endfor %}
  </tr>
{%- endfor %}
</table>

<h1>Unfilled</h1>
<div class="index">
  {%- for column in items|slice(3) %}
  <div class="col-{{ loop.index }}">
    <ul>
    {%- for item in column %}
      <li>{{ item }}</li>
    {%- endfor %}
    </ul>
  </div>
  {%- endfor %}
</div>

<h1>Filled</h1>
<div class="index">
  {%- for column in items|slice(3, 'missing') %}
  <div class="col-{{ loop.index }}">
    <ul>
    {%- for item in column %}
      <li>{{ item }}</li>
    {%- endfor %}
    </ul>
  </div>
  {%- endfor %}
</div>

<h1>Filled Table</h1>
<table>
  {%- for row in items|batch(3, '&nbsp;') %}
  <tr>
    {%- for column in row %}
    <td>{{ column }}</td>
    {%- endfor %}
  </tr>
  {%- endfor %}
</table>

<h1>Unfilled Table</h1>
<table>
  {%- for row in items|batch(3) %}
  <tr>
    {%- for column in row %}
    <td>{{ column }}</td>
    {%- endfor %}
    {%- if row|length < 3 %}
    <td colspan="{{ 3 - (row|length) }}">&nbsp;</td>
    {%- endif %}
  </tr>
  {%- endfor %}
</table>

<h1>Macros</h1>
{% macro foo seq %}
  <ul>
  {%- for item in seq %}
    <li>{{ caller(item=item) }}</li>
  {%- endfor %}
  </ul>
{% endmacro %}

{% call foo(items) -%}
  [{{ item }}]
{%- endcall %}
''')

start = time()
for _ in xrange(50):
    tmpl.render(
        items=range(200),
        table=[dict(a='1',b='2',c='3',d='4',e='5',f='6',g='7',h='8',i='9',j='10')
               for x in range(1000)]
    )
print time() - start
