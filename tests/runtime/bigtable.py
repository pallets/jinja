# -*- coding: utf-8 -*_
# Template language benchmarks
#
# Objective: Generate a 1000x10 HTML table as fast as possible.
# adapted for jinja 1
#
# Author: Jonas Borgström <jonas@edgewall.com>
# Author: Armin Ronacher <armin.ronacher@active-4.com>

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import cgi
import timeit
import jdebug
from StringIO import StringIO


try:
    from genshi.builder import tag
    from genshi.template import MarkupTemplate
    have_genshi = True
except ImportError:
    have_genshi = False

from jinja2 import Environment

try:
    from django.conf import settings
    settings.configure()
    from django.template import Context as DjangoContext
    from django.template import Template as DjangoTemplate
    have_django = True
except ImportError:
    have_django = False

try:
    from kid import Template as KidTemplate
    have_kid = True
except ImportError:
    have_kid = False

try:
    from Cheetah.Template import Template as CheetahTemplate
    have_cheetah = True
except ImportError:
    have_cheetah = False

try:
    from mako.template import Template as MakoTemplate
    have_mako = True
except ImportError:
    have_mako = False

table = [dict(zip('abcdefghij', map(unicode,range(1, 11))))
          for x in range(1000)]

if have_genshi:
    genshi_tmpl = MarkupTemplate("""
<table xmlns:py="http://genshi.edgewall.org/">
<tr py:for="row in table">
<td py:for="c in row.values()" py:content="c"/>
</tr>
</table>
""")

if have_kid:
    kid_tmpl = KidTemplate("""
<table xmlns:py="http://purl.org/kid/ns#">
<tr py:for="row in table">
<td py:for="c in row.values()" py:content="c"/>
</tr>
</table>
""")

if have_django:
    django_tmpl = DjangoTemplate("""
<table>
{% for row in table %}
<tr>{% for col in row.values %}<td>{{ col }}</td>{% endfor %}</tr>
{% endfor %}
</table>
""")

jinja_tmpl = Environment().from_string('''
<table>
{% for row in table -%}
<tr>{% for col in row.values() %}<td>{{ col }}</td>{% endfor %}</tr>
{% endfor %}
</table>
''')

if have_cheetah:
    cheetah_tmpl = CheetahTemplate('''
<table>
#for $row in $table
<tr>
#for $col in $row.values()
<td>$col</td>
#end for
</tr>
#end for
</table>
''', searchList=[{'table': table, 'escape': cgi.escape}])

if have_mako:
    mako_tmpl = MakoTemplate('''
<table>
% for row in table:
<tr>
% for col in row.values():
    <td>${col}</td>
% endfor
</tr>
% endfor
</table>
''')

def test_django():
    """Django Templates"""
    if not have_django:
        return
    context = DjangoContext({'table': table})
    django_tmpl.render(context)

def test_jinja():
    """Jinja Templates"""
    jinja_tmpl.render(table=table)

def test_genshi():
    """Genshi Templates"""
    if not have_genshi:
        return
    stream = genshi_tmpl.generate(table=table)
    stream.render('html', strip_whitespace=False)

def test_kid():
    """Kid Templates"""
    if not have_kid:
        return
    kid_tmpl.table = table
    kid_tmpl.serialize(output="html")

def test_cheetah():
    """Cheetah Templates"""
    if not have_cheetah:
        return
    cheetah_tmpl.respond()

def test_mako():
    """Mako Templates"""
    if not have_mako:
        return
    mako_tmpl.render(table=table)


def run(which=None, number=10):
    tests = ['test_django', 'test_jinja', 'test_kid', 'test_genshi',
             'test_cheetah', 'test_mako']

    if which:
        tests = filter(lambda n: n[5:] in which, tests)

    for test in [t for t in tests if hasattr(sys.modules[__name__], t)]:
        t = timeit.Timer(setup='from __main__ import %s;' % test,
                         stmt='%s()' % test)
        time = t.timeit(number=number) / number

        if time < 0.00001:
            result = '   (not installed?)'
        else:
            result = '%16.2f ms' % (1000 * time)
        print '%-35s %s' % (getattr(sys.modules[__name__], test).__doc__, result)


if __name__ == '__main__':
    which = [arg for arg in sys.argv[1:] if arg[0] != '-']

    if '-p' in sys.argv:
        from cProfile import Profile
        from pstats import Stats
        p = Profile()
        p.runcall(test_jinja)
        stats = Stats(p)
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats()
    else:
        run(which)
