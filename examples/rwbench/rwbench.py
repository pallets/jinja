# -*- coding: utf-8 -*-
"""
    RealWorldish Benchmark
    ~~~~~~~~~~~~~~~~~~~~~~

    A more real-world benchmark of Jinja2.  Like the other benchmark in the
    Jinja2 repository this has no real-world usefulnes (despite the name).
    Just go away and ignore it.  NOW!

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import sys
from os.path import join, dirname, abspath
ROOT = abspath(dirname(__file__))

from random import choice, randrange
from datetime import datetime
from timeit import Timer
from jinja2 import Environment, FileSystemLoader
from jinja2.utils import generate_lorem_ipsum
from mako.lookup import TemplateLookup


def dateformat(x):
    return x.strftime('%Y-%m-%d')


jinja_env = Environment(loader=FileSystemLoader(join(ROOT, 'jinja')))
jinja_env.filters['dateformat'] = dateformat
mako_lookup = TemplateLookup(directories=[join(ROOT, 'mako')])

class Article(object):

    def __init__(self, id):
        self.id = id
        self.href = '/article/%d' % self.id
        self.title = generate_lorem_ipsum(1, False, 5, 10)
        self.user = choice(users)
        self.body = generate_lorem_ipsum()
        self.pub_date = datetime.utcfromtimestamp(randrange(10 ** 9, 2 * 10 ** 9))
        self.published = True


class User(object):

    def __init__(self, username):
        self.href = '/user/%s' % username
        self.username = username


users = map(User, [u'John Doe', u'Jane Doe', u'Peter Somewhat'])
articles = map(Article, range(20))
navigation = [
    ('index',           'Index'),
    ('about',           'About'),
    ('foo?bar=1',       'Foo with Bar'),
    ('foo?bar=2&s=x',   'Foo with X'),
    ('blah',            'Blub Blah'),
    ('hehe',            'Haha'),
] * 5

context = dict(users=users, articles=articles, page_navigation=navigation)


jinja_template = jinja_env.get_template('index.html')
mako_template = mako_lookup.get_template('index.html')


def test_jinja():
    jinja_template.render(context)

def test_mako():
    mako_template.render_unicode(**context)


from djangoext import django_loader, DjangoContext
django_template = django_loader.get_template('index.html')
def test_django():
    django_template.render(DjangoContext(context))


if __name__ == '__main__':
    sys.stdout.write('Realworldish Benchmark:\n')
    for test in 'jinja', 'mako', 'django':
        t = Timer(setup='from __main__ import test_%s as bench' % test,
                  stmt='bench()')
        sys.stdout.write(' >> %-20s<running>' % test)
        sys.stdout.flush()
        sys.stdout.write('\r    %-20s%.4f seconds\n' % (test, t.timeit(number=200) / 200))
