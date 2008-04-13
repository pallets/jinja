# -*- coding: utf-8 -*-
"""
    unit test for the i18n functions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from jinja2 import Environment, DictLoader

templates = {
    'master.html': '<title>{{ page_title|default(_("missing")) }}</title>'
                   '{% block body %}{% endblock %}',
    'child.html': '{% extends "master.html" %}{% block body %}'
                  '{% trans "watch out" %}{% endblock %}',
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


class SimpleTranslator(object):
    """Yes i know it's only suitable for english and german but
    that's a stupid unittest..."""

    def __init__(self, language):
        self.strings = languages.get(language, {})

    def gettext(self, string):
        return self.strings.get(string, string)

    def ngettext(self, s, p, n):
        if n != 1:
            return self.strings.get(p, p)
        return self.strings.get(s, s)


class I18NEnvironment(Environment):

    def __init__(self):
        super(I18NEnvironment, self).__init__(loader=DictLoader(templates))

    def get_translator(self, context):
        return SimpleTranslator(context['LANGUAGE'] or 'en')


i18n_env = I18NEnvironment()


def test_factory():
    def factory(context):
        return SimpleTranslator(context['LANGUAGE'] or 'en')
    env = Environment(translator_factory=factory)
    tmpl = env.from_string('{% trans "watch out" %}')
    assert tmpl.render(LANGUAGE='de') == 'pass auf'


def test_get_translations():
    trans = list(i18n_env.get_translations('child.html'))
    assert len(trans) == 1
    assert trans[0] == (1, u'watch out', None)


def test_get_translations_for_string():
    trans = list(i18n_env.get_translations('master.html'))
    assert len(trans) == 1
    assert trans[0] == (1, u'missing', None)


def test_trans():
    tmpl = i18n_env.get_template('child.html')
    assert tmpl.render(LANGUAGE='de') == '<title>fehlend</title>pass auf'


def test_trans_plural():
    tmpl = i18n_env.get_template('plural.html')
    assert tmpl.render(LANGUAGE='de', user_count=1) == 'Ein Benutzer online'
    assert tmpl.render(LANGUAGE='de', user_count=2) == '2 Benutzer online'


def test_trans_stringformatting():
    tmpl = i18n_env.get_template('stringformat.html')
    assert tmpl.render(LANGUAGE='de', user_count=5) == 'Benutzer: 5'
