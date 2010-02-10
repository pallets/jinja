# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.ext
    ~~~~~~~~~~~~~~~~~~~~

    Tests for the extensions.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import re
import unittest

from jinja2.testsuite import JinjaTestCase, filesystem_loader

from jinja2 import Environment, DictLoader, contextfunction, nodes
from jinja2.exceptions import TemplateAssertionError
from jinja2.ext import Extension
from jinja2.lexer import Token, count_newlines
from jinja2.utils import next

# 2.x / 3.x
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO


importable_object = 23

_gettext_re = re.compile(r'_\((.*?)\)(?s)')


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


class TestExtension(Extension):
    tags = set(['test'])
    ext_attr = 42

    def parse(self, parser):
        return nodes.Output([self.call_method('_dump', [
            nodes.EnvironmentAttribute('sandboxed'),
            self.attr('ext_attr'),
            nodes.ImportedName(__name__ + '.importable_object'),
            nodes.ContextReference()
        ])]).set_lineno(next(parser.stream).lineno)

    def _dump(self, sandboxed, ext_attr, imported_object, context):
        return '%s|%s|%s|%s' % (
            sandboxed,
            ext_attr,
            imported_object,
            context.blocks
        )


class PreprocessorExtension(Extension):

    def preprocess(self, source, name, filename=None):
        return source.replace('[[TEST]]', '({{ foo }})')


class StreamFilterExtension(Extension):

    def filter_stream(self, stream):
        for token in stream:
            if token.type == 'data':
                for t in self.interpolate(token):
                    yield t
            else:
                yield token

    def interpolate(self, token):
        pos = 0
        end = len(token.value)
        lineno = token.lineno
        while 1:
            match = _gettext_re.search(token.value, pos)
            if match is None:
                break
            value = token.value[pos:match.start()]
            if value:
                yield Token(lineno, 'data', value)
            lineno += count_newlines(token.value)
            yield Token(lineno, 'variable_begin', None)
            yield Token(lineno, 'name', 'gettext')
            yield Token(lineno, 'lparen', None)
            yield Token(lineno, 'string', match.group(1))
            yield Token(lineno, 'rparen', None)
            yield Token(lineno, 'variable_end', None)
            pos = match.end()
        if pos < end:
            yield Token(lineno, 'data', token.value[pos:])


class ExtensionsTestCase(JinjaTestCase):

    def test_loop_controls(self):
        env = Environment(extensions=['jinja2.ext.loopcontrols'])

        tmpl = env.from_string('''
            {%- for item in [1, 2, 3, 4] %}
                {%- if item % 2 == 0 %}{% continue %}{% endif -%}
                {{ item }}
            {%- endfor %}''')
        assert tmpl.render() == '13'

        tmpl = env.from_string('''
            {%- for item in [1, 2, 3, 4] %}
                {%- if item > 2 %}{% break %}{% endif -%}
                {{ item }}
            {%- endfor %}''')
        assert tmpl.render() == '12'

    def test_do(self):
        env = Environment(extensions=['jinja2.ext.do'])
        tmpl = env.from_string('''
            {%- set items = [] %}
            {%- for char in "foo" %}
                {%- do items.append(loop.index0 ~ char) %}
            {%- endfor %}{{ items|join(', ') }}''')
        assert tmpl.render() == '0f, 1o, 2o'

    def test_with(self):
        env = Environment(extensions=['jinja2.ext.with_'])
        tmpl = env.from_string('''\
        {% with a=42, b=23 -%}
            {{ a }} = {{ b }}
        {% endwith -%}
            {{ a }} = {{ b }}\
        ''')
        assert [x.strip() for x in tmpl.render(a=1, b=2).splitlines()] \
            == ['42 = 23', '1 = 2']

    def test_extension_nodes(self):
        env = Environment(extensions=[TestExtension])
        tmpl = env.from_string('{% test %}')
        assert tmpl.render() == 'False|42|23|{}'

    def test_identifier(self):
        assert TestExtension.identifier == __name__ + '.TestExtension'

    def test_rebinding(self):
        original = Environment(extensions=[TestExtension])
        overlay = original.overlay()
        for env in original, overlay:
            for ext in env.extensions.itervalues():
                assert ext.environment is env

    def test_preprocessor_extension(self):
        env = Environment(extensions=[PreprocessorExtension])
        tmpl = env.from_string('{[[TEST]]}')
        assert tmpl.render(foo=42) == '{(42)}'

    def test_streamfilter_extension(self):
        env = Environment(extensions=[StreamFilterExtension])
        env.globals['gettext'] = lambda x: x.upper()
        tmpl = env.from_string('Foo _(bar) Baz')
        out = tmpl.render()
        assert out == 'Foo BAR Baz'


class InternationalizationTestCase(JinjaTestCase):

    def test_trans(self):
        tmpl = i18n_env.get_template('child.html')
        assert tmpl.render(LANGUAGE='de') == '<title>fehlend</title>pass auf'

    def test_trans_plural(self):
        tmpl = i18n_env.get_template('plural.html')
        assert tmpl.render(LANGUAGE='de', user_count=1) == 'Ein Benutzer online'
        assert tmpl.render(LANGUAGE='de', user_count=2) == '2 Benutzer online'

    def test_complex_plural(self):
        tmpl = i18n_env.from_string('{% trans foo=42, count=2 %}{{ count }} item{% '
                                    'pluralize count %}{{ count }} items{% endtrans %}')
        assert tmpl.render() == '2 items'
        self.assert_raises(TemplateAssertionError, i18n_env.from_string,
                           '{% trans foo %}...{% pluralize bar %}...{% endtrans %}')

    def test_trans_stringformatting(self):
        tmpl = i18n_env.get_template('stringformat.html')
        assert tmpl.render(LANGUAGE='de', user_count=5) == 'Benutzer: 5'

    def test_extract(self):
        from jinja2.ext import babel_extract
        source = BytesIO('''
        {{ gettext('Hello World') }}
        {% trans %}Hello World{% endtrans %}
        {% trans %}{{ users }} user{% pluralize %}{{ users }} users{% endtrans %}
        '''.encode('ascii')) # make python 3 happy
        assert list(babel_extract(source, ('gettext', 'ngettext', '_'), [], {})) == [
            (2, 'gettext', u'Hello World', []),
            (3, 'gettext', u'Hello World', []),
            (4, 'ngettext', (u'%(users)s user', u'%(users)s users', None), [])
        ]

    def test_comment_extract(self):
        from jinja2.ext import babel_extract
        source = BytesIO('''
        {# trans first #}
        {{ gettext('Hello World') }}
        {% trans %}Hello World{% endtrans %}{# trans second #}
        {#: third #}
        {% trans %}{{ users }} user{% pluralize %}{{ users }} users{% endtrans %}
        '''.encode('utf-8')) # make python 3 happy
        assert list(babel_extract(source, ('gettext', 'ngettext', '_'), ['trans', ':'], {})) == [
            (3, 'gettext', u'Hello World', ['first']),
            (4, 'gettext', u'Hello World', ['second']),
            (6, 'ngettext', (u'%(users)s user', u'%(users)s users', None), ['third'])
        ]


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExtensionsTestCase))
    suite.addTest(unittest.makeSuite(InternationalizationTestCase))
    return suite
