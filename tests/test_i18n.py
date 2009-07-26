# -*- coding: utf-8 -*-
"""
    unit test for the i18n functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2009 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, DictLoader, contextfunction
from jinja2.exceptions import TemplateAssertionError

from nose.tools import assert_raises

templates = {
    'master.html': '<title>{{ page_title|default(_("missing")) }}</title>'
                   '{% block body %}{% endblock %}',
    'child.html': '{% extends "master.html" %}{% block body %}'
                  '{% trans %}watch out{% endtrans %}{% endblock %}',
    'plural.html': '{% trans user_count %}One user online{% pluralize %}'
                   '{{ user_count }} users online{% endtrans %}',
    'stringformat.html': '{{ _("User: %d")|format(user_count) }}'
}


languages = {
    'de': {
        'missing':                      'fehlend',
        'watch out':                    'pass auf',
        'One user online':              'Ein Benutzer online',
        '%(user_count)s users online':  '%(user_count)s Benutzer online',
        'User: %d':                     'Benutzer: %d'
    }
}


@contextfunction
def gettext(context, string):
    language = context.get('LANGUAGE', 'en')
    return languages.get(language, {}).get(string, string)


@contextfunction
def ngettext(context, s, p, n):
    language = context.get('LANGUAGE', 'en')
    if n != 1:
        return languages.get(language, {}).get(p, p)
    return languages.get(language, {}).get(s, s)


i18n_env = Environment(
    loader=DictLoader(templates),
    extensions=['jinja2.ext.i18n']
)
i18n_env.globals.update({
    '_':            gettext,
    'gettext':      gettext,
    'ngettext':     ngettext
})


def test_trans():
    tmpl = i18n_env.get_template('child.html')
    assert tmpl.render(LANGUAGE='de') == '<title>fehlend</title>pass auf'


def test_trans_plural():
    tmpl = i18n_env.get_template('plural.html')
    assert tmpl.render(LANGUAGE='de', user_count=1) == 'Ein Benutzer online'
    assert tmpl.render(LANGUAGE='de', user_count=2) == '2 Benutzer online'


def test_complex_plural():
    tmpl = i18n_env.from_string('{% trans foo=42, count=2 %}{{ count }} item{% '
                                'pluralize count %}{{ count }} items{% endtrans %}')
    assert tmpl.render() == '2 items'
    assert_raises(TemplateAssertionError, i18n_env.from_string,
                 '{% trans foo %}...{% pluralize bar %}...{% endtrans %}')


def test_trans_stringformatting():
    tmpl = i18n_env.get_template('stringformat.html')
    assert tmpl.render(LANGUAGE='de', user_count=5) == 'Benutzer: 5'


def test_extract():
    from jinja2.ext import babel_extract
    from StringIO import StringIO
    source = StringIO('''
    {{ gettext('Hello World') }}
    {% trans %}Hello World{% endtrans %}
    {% trans %}{{ users }} user{% pluralize %}{{ users }} users{% endtrans %}
    ''')
    assert list(babel_extract(source, ('gettext', 'ngettext', '_'), [], {})) == [
        (2, 'gettext', u'Hello World', []),
        (3, 'gettext', u'Hello World', []),
        (4, 'ngettext', (u'%(users)s user', u'%(users)s users', None), [])
    ]
