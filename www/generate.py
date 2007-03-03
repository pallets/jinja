#!/usr/bin/env python
"""
    jinja webpage generator
    ~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
from codecs import open
from jinja import Environment, FileSystemLoader
from jinja.filters import stringfilter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


formatter = HtmlFormatter(cssclass='syntax', encoding=None, style='pastie')

env = Environment('<%', '%>', '<%=', '%>', loader=FileSystemLoader('.'), trim_blocks=True)
env.filters['pygmentize'] = stringfilter(lambda v, l:
    highlight(v.strip(), get_lexer_by_name(l), formatter))


def get_files(folder):
    for fn in os.listdir(folder):
        fn = os.path.join(folder, fn)
        if os.path.isdir(fn):
            for item in get_files(fn):
                yield item
        elif fn.endswith('.tmpl'):
            yield fn


for filename in get_files('.'):
    root = './' + ''.join(['../' for _ in os.path.dirname(filename).
                           split(os.path.sep)[1:]])

    t = env.get_template(filename)
    f = open(filename[:-5] + '.html', 'w', 'utf-8')
    f.write(t.render(
        file_id=filename[2:-5],
        root=root
    ))
    f.close()

f = file('static/pygments.css', 'w')
f.write(formatter.get_style_defs('.syntax'))
f.close()
