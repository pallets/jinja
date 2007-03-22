#!/usr/bin/env python
"""
    jinja webpage generator
    ~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import sys
import re
from codecs import open
from jinja import Environment, FileSystemLoader
from jinja.filters import stringfilter
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


_data_re = re.compile(
    r'<!-- TITLE -->(?P<page_title>.*?)<!-- ENDTITLE -->.*?'
    r'<!-- TOC -->(?P<page_toc>.*?)<!-- ENDTOC -->.*?'
    r'<!-- BODY -->(?P<page_body>.*?)<!-- ENDBODY -->(?sm)'
)

formatter = HtmlFormatter(cssclass='syntax', encoding=None, style='pastie')

env = Environment('<%', '%>', '<%=', '%>', loader=FileSystemLoader('.',
    cache_folder='/tmp'), trim_blocks=True)
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


# generate static stuff
for filename in get_files('.'):
    root = './' + ''.join(['../' for _ in os.path.dirname(filename).
                           split(os.path.sep)[1:]])

    t = env.get_template(filename)
    f = open(filename[:-5] + '.html', 'w', 'utf-8')
    f.write(t.render(
        root=root
    ))
    f.close()
    print filename

# generate pygments stylesheet
f = file('static/pygments.css', 'w')
f.write(formatter.get_style_defs('.syntax'))
f.close()

# generate documentation
os.system(sys.executable + ' ../docs/generate.py documentation true')

# render documentation with documentation template
tmpl = env.get_template('documentation/item.tmpl')

for filename in os.listdir('documentation'):
    if not filename.endswith('.html'):
        continue
    filename = 'documentation/' + filename
    f = open(filename, 'r', 'utf-8')
    try:
        data = f.read()
    finally:
        f.close()
    match = _data_re.search(data)
    if match is None:
        continue
    data = match.groupdict()
    data['page_toc'] = data['page_toc'].strip()
    if data['page_toc'].count('</li') < 2:
        data['page_toc'] = ''
    f = open(filename, 'w', 'utf-8')
    f.write(tmpl.render(
        root='./../',
        **data
    ))
    f.close()
    print 'postprocessed', filename
