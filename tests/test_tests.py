# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.tests
    ~~~~~~~~~~~~~~~~~~~~~~

    Who tests the tests?

    :copyright: (c) 2017 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import pytest

from jinja2 import Markup, Environment


@pytest.mark.test_tests
class TestTestsCase(object):

    def test_defined(self, env):
        tmpl = env.from_string('{{ missing is defined }}|'
                               '{{ true is defined }}')
        assert tmpl.render() == 'False|True'

    def test_even(self, env):
        tmpl = env.from_string('''{{ 1 is even }}|{{ 2 is even }}''')
        assert tmpl.render() == 'False|True'

    def test_odd(self, env):
        tmpl = env.from_string('''{{ 1 is odd }}|{{ 2 is odd }}''')
        assert tmpl.render() == 'True|False'

    def test_lower(self, env):
        tmpl = env.from_string('''{{ "foo" is lower }}|{{ "FOO" is lower }}''')
        assert tmpl.render() == 'True|False'

    def test_typechecks(self, env):
        tmpl = env.from_string('''
            {{ 42 is undefined }}
            {{ 42 is defined }}
            {{ 42 is none }}
            {{ none is none }}
            {{ 42 is number }}
            {{ 42 is string }}
            {{ "foo" is string }}
            {{ "foo" is sequence }}
            {{ [1] is sequence }}
            {{ range is callable }}
            {{ 42 is callable }}
            {{ range(5) is iterable }}
            {{ {} is mapping }}
            {{ mydict is mapping }}
            {{ [] is mapping }}
            {{ 10 is number }}
            {{ (10 ** 100) is number }}
            {{ 3.14159 is number }}
            {{ complex is number }}
        ''')

        class MyDict(dict):
            pass

        assert tmpl.render(mydict=MyDict(), complex=complex(1, 2)).split() == [
            'False', 'True', 'False', 'True', 'True', 'False',
            'True', 'True', 'True', 'True', 'False', 'True',
            'True', 'True', 'False', 'True', 'True', 'True', 'True'
        ]

    def test_sequence(self, env):
        tmpl = env.from_string(
            '{{ [1, 2, 3] is sequence }}|'
            '{{ "foo" is sequence }}|'
            '{{ 42 is sequence }}'
        )
        assert tmpl.render() == 'True|True|False'

    def test_upper(self, env):
        tmpl = env.from_string('{{ "FOO" is upper }}|{{ "foo" is upper }}')
        assert tmpl.render() == 'True|False'

    def test_equalto(self, env):
        tmpl = env.from_string(
            '{{ foo is eq 12 }}|'
            '{{ foo is eq 0 }}|'
            '{{ foo is eq (3 * 4) }}|'
            '{{ bar is eq "baz" }}|'
            '{{ bar is eq "zab" }}|'
            '{{ bar is eq ("ba" + "z") }}|'
            '{{ bar is eq bar }}|'
            '{{ bar is eq foo }}'
        )
        assert tmpl.render(foo=12, bar="baz") \
            == 'True|False|True|True|False|True|True|False'

    @pytest.mark.parametrize('op,expect', (
        ('eq 2', True),
        ('eq 3', False),
        ('ne 3', True),
        ('ne 2', False),
        ('lt 3', True),
        ('lt 2', False),
        ('le 2', True),
        ('le 1', False),
        ('gt 1', True),
        ('gt 2', False),
        ('ge 2', True),
        ('ge 3', False),
    ))
    def test_compare_aliases(self, env, op, expect):
        t = env.from_string('{{{{ 2 is {op} }}}}'.format(op=op))
        assert t.render() == str(expect)

    def test_sameas(self, env):
        tmpl = env.from_string('{{ foo is sameas false }}|'
                               '{{ 0 is sameas false }}')
        assert tmpl.render(foo=False) == 'True|False'

    def test_no_paren_for_arg1(self, env):
        tmpl = env.from_string('{{ foo is sameas none }}')
        assert tmpl.render(foo=None) == 'True'

    def test_escaped(self, env):
        env = Environment(autoescape=True)
        tmpl = env.from_string('{{ x is escaped }}|{{ y is escaped }}')
        assert tmpl.render(x='foo', y=Markup('foo')) == 'False|True'

    def test_greaterthan(self, env):
        tmpl = env.from_string('{{ 1 is greaterthan 0 }}|'
                               '{{ 0 is greaterthan 1 }}')
        assert tmpl.render() == 'True|False'

    def test_lessthan(self, env):
        tmpl = env.from_string('{{ 0 is lessthan 1 }}|'
                               '{{ 1 is lessthan 0 }}')
        assert tmpl.render() == 'True|False'

    def test_multiple_tests(self):
        items = []
        def matching(x, y):
            items.append((x, y))
            return False
        env = Environment()
        env.tests['matching'] = matching
        tmpl = env.from_string("{{ 'us-west-1' is matching "
                               "'(us-east-1|ap-northeast-1)' "
                               "or 'stage' is matching '(dev|stage)' }}")
        assert tmpl.render() == 'False'
        assert items == [('us-west-1', '(us-east-1|ap-northeast-1)'),
                         ('stage', '(dev|stage)')]

    def test_in(self, env):
        tmpl = env.from_string('{{ "o" is in "foo" }}|'
                               '{{ "foo" is in "foo" }}|'
                               '{{ "b" is in "foo" }}|'
                               '{{ 1 is in ((1, 2)) }}|'
                               '{{ 3 is in ((1, 2)) }}|'
                               '{{ 1 is in [1, 2] }}|'
                               '{{ 3 is in [1, 2] }}|'
                               '{{ "foo" is in {"foo": 1}}}|'
                               '{{ "baz" is in {"bar": 1}}}')
        assert tmpl.render() \
            == 'True|True|False|True|False|True|False|True|False'
