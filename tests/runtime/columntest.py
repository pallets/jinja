import jdebug
from jinja2 import from_string


template = from_string(u'''\
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
</table>''')

print template.render(items=range(16))
