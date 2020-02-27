# -*- coding: utf-8 -*-
import random
from collections import namedtuple

import pytest

from jinja2 import Environment
from jinja2 import Markup
from jinja2 import StrictUndefined
from jinja2 import UndefinedError
from jinja2._compat import implements_to_string
from jinja2._compat import text_type


@implements_to_string
class Magic(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return text_type(self.value)


@implements_to_string
class Magic2(object):
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2

    def __str__(self):
        return u"(%s,%s)" % (text_type(self.value1), text_type(self.value2))


class TestFilter(object):
    def test_filter_calling(self, env):
        rv = env.call_filter("sum", [1, 2, 3])
        assert rv == 6

    def test_capitalize(self, env):
        tmpl = env.from_string('{{ "foo bar"|capitalize }}')
        assert tmpl.render() == "Foo bar"

    def test_center(self, env):
        tmpl = env.from_string('{{ "foo"|center(9) }}')
        assert tmpl.render() == "   foo   "

    def test_default(self, env):
        tmpl = env.from_string(
            "{{ missing|default('no') }}|{{ false|default('no') }}|"
            "{{ false|default('no', true) }}|{{ given|default('no') }}"
        )
        assert tmpl.render(given="yes") == "no|False|no|yes"

    @pytest.mark.parametrize(
        "args,expect",
        (
            ("", "[('aa', 0), ('AB', 3), ('b', 1), ('c', 2)]"),
            ("true", "[('AB', 3), ('aa', 0), ('b', 1), ('c', 2)]"),
            ('by="value"', "[('aa', 0), ('b', 1), ('c', 2), ('AB', 3)]"),
            ("reverse=true", "[('c', 2), ('b', 1), ('AB', 3), ('aa', 0)]"),
        ),
    )
    def test_dictsort(self, env, args, expect):
        t = env.from_string("{{{{ foo|dictsort({args}) }}}}".format(args=args))
        out = t.render(foo={"aa": 0, "b": 1, "c": 2, "AB": 3})
        assert out == expect

    def test_batch(self, env):
        tmpl = env.from_string("{{ foo|batch(3)|list }}|{{ foo|batch(3, 'X')|list }}")
        out = tmpl.render(foo=list(range(10)))
        assert out == (
            "[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]|"
            "[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 'X', 'X']]"
        )

    def test_slice(self, env):
        tmpl = env.from_string("{{ foo|slice(3)|list }}|{{ foo|slice(3, 'X')|list }}")
        out = tmpl.render(foo=list(range(10)))
        assert out == (
            "[[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]]|"
            "[[0, 1, 2, 3], [4, 5, 6, 'X'], [7, 8, 9, 'X']]"
        )

    def test_escape(self, env):
        tmpl = env.from_string("""{{ '<">&'|escape }}""")
        out = tmpl.render()
        assert out == "&lt;&#34;&gt;&amp;"

    @pytest.mark.parametrize(
        ("chars", "expect"), [(None, "..stays.."), (".", "  ..stays"), (" .", "stays")]
    )
    def test_trim(self, env, chars, expect):
        tmpl = env.from_string("{{ foo|trim(chars) }}")
        out = tmpl.render(foo="  ..stays..", chars=chars)
        assert out == expect

    def test_striptags(self, env):
        tmpl = env.from_string("""{{ foo|striptags }}""")
        out = tmpl.render(
            foo='  <p>just a small   \n <a href="#">'
            "example</a> link</p>\n<p>to a webpage</p> "
            "<!-- <p>and some commented stuff</p> -->"
        )
        assert out == "just a small example link to a webpage"

    def test_filesizeformat(self, env):
        tmpl = env.from_string(
            "{{ 100|filesizeformat }}|"
            "{{ 1000|filesizeformat }}|"
            "{{ 1000000|filesizeformat }}|"
            "{{ 1000000000|filesizeformat }}|"
            "{{ 1000000000000|filesizeformat }}|"
            "{{ 100|filesizeformat(true) }}|"
            "{{ 1000|filesizeformat(true) }}|"
            "{{ 1000000|filesizeformat(true) }}|"
            "{{ 1000000000|filesizeformat(true) }}|"
            "{{ 1000000000000|filesizeformat(true) }}"
        )
        out = tmpl.render()
        assert out == (
            "100 Bytes|1.0 kB|1.0 MB|1.0 GB|1.0 TB|100 Bytes|"
            "1000 Bytes|976.6 KiB|953.7 MiB|931.3 GiB"
        )

    def test_filesizeformat_issue59(self, env):
        tmpl = env.from_string(
            "{{ 300|filesizeformat }}|"
            "{{ 3000|filesizeformat }}|"
            "{{ 3000000|filesizeformat }}|"
            "{{ 3000000000|filesizeformat }}|"
            "{{ 3000000000000|filesizeformat }}|"
            "{{ 300|filesizeformat(true) }}|"
            "{{ 3000|filesizeformat(true) }}|"
            "{{ 3000000|filesizeformat(true) }}"
        )
        out = tmpl.render()
        assert out == (
            "300 Bytes|3.0 kB|3.0 MB|3.0 GB|3.0 TB|300 Bytes|2.9 KiB|2.9 MiB"
        )

    def test_first(self, env):
        tmpl = env.from_string("{{ foo|first }}")
        out = tmpl.render(foo=list(range(10)))
        assert out == "0"

    @pytest.mark.parametrize(
        ("value", "expect"), (("42", "42.0"), ("abc", "0.0"), ("32.32", "32.32"),)
    )
    def test_float(self, env, value, expect):
        t = env.from_string("{{ '%s'|float }}" % value)
        assert t.render() == expect

    def test_float_default(self, env):
        t = env.from_string("{{ value|float(default=1.0) }}")
        assert t.render(value="abc") == "1.0"

    def test_format(self, env):
        tmpl = env.from_string("""{{ "%s|%s"|format("a", "b") }}""")
        out = tmpl.render()
        assert out == "a|b"

    @staticmethod
    def _test_indent_multiline_template(env, markup=False):
        text = "\n".join(["", "foo bar", '"baz"', ""])
        if markup:
            text = Markup(text)
        t = env.from_string("{{ foo|indent(2, false, false) }}")
        assert t.render(foo=text) == '\n  foo bar\n  "baz"\n'
        t = env.from_string("{{ foo|indent(2, false, true) }}")
        assert t.render(foo=text) == '\n  foo bar\n  "baz"\n  '
        t = env.from_string("{{ foo|indent(2, true, false) }}")
        assert t.render(foo=text) == '  \n  foo bar\n  "baz"\n'
        t = env.from_string("{{ foo|indent(2, true, true) }}")
        assert t.render(foo=text) == '  \n  foo bar\n  "baz"\n  '

    def test_indent(self, env):
        self._test_indent_multiline_template(env)
        t = env.from_string('{{ "jinja"|indent }}')
        assert t.render() == "jinja"
        t = env.from_string('{{ "jinja"|indent(first=true) }}')
        assert t.render() == "    jinja"
        t = env.from_string('{{ "jinja"|indent(blank=true) }}')
        assert t.render() == "jinja"

    def test_indent_markup_input(self, env):
        """
        Tests cases where the filter input is a Markup type
        """
        self._test_indent_multiline_template(env, markup=True)

    @pytest.mark.parametrize(
        ("value", "expect"),
        (
            ("42", "42"),
            ("abc", "0"),
            ("32.32", "32"),
            ("12345678901234567890", "12345678901234567890"),
        ),
    )
    def test_int(self, env, value, expect):
        t = env.from_string("{{ '%s'|int }}" % value)
        assert t.render() == expect

    @pytest.mark.parametrize(
        ("value", "base", "expect"),
        (("0x4d32", 16, "19762"), ("011", 8, "9"), ("0x33Z", 16, "0"),),
    )
    def test_int_base(self, env, value, base, expect):
        t = env.from_string("{{ '%s'|int(base=%d) }}" % (value, base))
        assert t.render() == expect

    def test_int_default(self, env):
        t = env.from_string("{{ value|int(default=1) }}")
        assert t.render(value="abc") == "1"

    def test_int_special_method(self, env):
        class IntIsh(object):
            def __int__(self):
                return 42

        t = env.from_string("{{ value|int }}")
        assert t.render(value=IntIsh()) == "42"

    def test_join(self, env):
        tmpl = env.from_string('{{ [1, 2, 3]|join("|") }}')
        out = tmpl.render()
        assert out == "1|2|3"

        env2 = Environment(autoescape=True)
        tmpl = env2.from_string('{{ ["<foo>", "<span>foo</span>"|safe]|join }}')
        assert tmpl.render() == "&lt;foo&gt;<span>foo</span>"

    def test_join_attribute(self, env):
        User = namedtuple("User", "username")
        tmpl = env.from_string("""{{ users|join(', ', 'username') }}""")
        assert tmpl.render(users=map(User, ["foo", "bar"])) == "foo, bar"

    def test_last(self, env):
        tmpl = env.from_string("""{{ foo|last }}""")
        out = tmpl.render(foo=list(range(10)))
        assert out == "9"

    def test_length(self, env):
        tmpl = env.from_string("""{{ "hello world"|length }}""")
        out = tmpl.render()
        assert out == "11"

    def test_lower(self, env):
        tmpl = env.from_string("""{{ "FOO"|lower }}""")
        out = tmpl.render()
        assert out == "foo"

    def test_pprint(self, env):
        from pprint import pformat

        tmpl = env.from_string("""{{ data|pprint }}""")
        data = list(range(1000))
        assert tmpl.render(data=data) == pformat(data)

    def test_random(self, env, request):
        # restore the random state when the test ends
        state = random.getstate()
        request.addfinalizer(lambda: random.setstate(state))
        # generate the random values from a known seed
        random.seed("jinja")
        expected = [random.choice("1234567890") for _ in range(10)]

        # check that the random sequence is generated again by a template
        # ensures that filter result is not constant folded
        random.seed("jinja")
        t = env.from_string('{{ "1234567890"|random }}')

        for value in expected:
            assert t.render() == value

    def test_reverse(self, env):
        tmpl = env.from_string(
            "{{ 'foobar'|reverse|join }}|{{ [1, 2, 3]|reverse|list }}"
        )
        assert tmpl.render() == "raboof|[3, 2, 1]"

    def test_string(self, env):
        x = [1, 2, 3, 4, 5]
        tmpl = env.from_string("""{{ obj|string }}""")
        assert tmpl.render(obj=x) == text_type(x)

    def test_title(self, env):
        tmpl = env.from_string("""{{ "foo bar"|title }}""")
        assert tmpl.render() == "Foo Bar"
        tmpl = env.from_string("""{{ "foo's bar"|title }}""")
        assert tmpl.render() == "Foo's Bar"
        tmpl = env.from_string("""{{ "foo   bar"|title }}""")
        assert tmpl.render() == "Foo   Bar"
        tmpl = env.from_string("""{{ "f bar f"|title }}""")
        assert tmpl.render() == "F Bar F"
        tmpl = env.from_string("""{{ "foo-bar"|title }}""")
        assert tmpl.render() == "Foo-Bar"
        tmpl = env.from_string("""{{ "foo\tbar"|title }}""")
        assert tmpl.render() == "Foo\tBar"
        tmpl = env.from_string("""{{ "FOO\tBAR"|title }}""")
        assert tmpl.render() == "Foo\tBar"
        tmpl = env.from_string("""{{ "foo (bar)"|title }}""")
        assert tmpl.render() == "Foo (Bar)"
        tmpl = env.from_string("""{{ "foo {bar}"|title }}""")
        assert tmpl.render() == "Foo {Bar}"
        tmpl = env.from_string("""{{ "foo [bar]"|title }}""")
        assert tmpl.render() == "Foo [Bar]"
        tmpl = env.from_string("""{{ "foo <bar>"|title }}""")
        assert tmpl.render() == "Foo <Bar>"

        class Foo:
            def __str__(self):
                return "foo-bar"

        tmpl = env.from_string("""{{ data|title }}""")
        out = tmpl.render(data=Foo())
        assert out == "Foo-Bar"

    def test_truncate(self, env):
        tmpl = env.from_string(
            '{{ data|truncate(15, true, ">>>") }}|'
            '{{ data|truncate(15, false, ">>>") }}|'
            "{{ smalldata|truncate(15) }}"
        )
        out = tmpl.render(data="foobar baz bar" * 1000, smalldata="foobar baz bar")
        msg = "Current output: %s" % out
        assert out == "foobar baz b>>>|foobar baz>>>|foobar baz bar", msg

    def test_truncate_very_short(self, env):
        tmpl = env.from_string(
            '{{ "foo bar baz"|truncate(9) }}|{{ "foo bar baz"|truncate(9, true) }}'
        )
        out = tmpl.render()
        assert out == "foo bar baz|foo bar baz", out

    def test_truncate_end_length(self, env):
        tmpl = env.from_string('{{ "Joel is a slug"|truncate(7, true) }}')
        out = tmpl.render()
        assert out == "Joel...", "Current output: %s" % out

    def test_upper(self, env):
        tmpl = env.from_string('{{ "foo"|upper }}')
        assert tmpl.render() == "FOO"

    def test_urlize(self, env):
        tmpl = env.from_string('{{ "foo http://www.example.com/ bar"|urlize }}')
        assert tmpl.render() == (
            'foo <a href="http://www.example.com/" rel="noopener">'
            "http://www.example.com/</a> bar"
        )

    def test_urlize_rel_policy(self):
        env = Environment()
        env.policies["urlize.rel"] = None
        tmpl = env.from_string('{{ "foo http://www.example.com/ bar"|urlize }}')
        assert tmpl.render() == (
            'foo <a href="http://www.example.com/">http://www.example.com/</a> bar'
        )

    def test_urlize_target_parameter(self, env):
        tmpl = env.from_string(
            '{{ "foo http://www.example.com/ bar"|urlize(target="_blank") }}'
        )
        assert (
            tmpl.render()
            == 'foo <a href="http://www.example.com/" rel="noopener" target="_blank">'
            "http://www.example.com/</a> bar"
        )

    def test_wordcount(self, env):
        tmpl = env.from_string('{{ "foo bar baz"|wordcount }}')
        assert tmpl.render() == "3"

        strict_env = Environment(undefined=StrictUndefined)
        t = strict_env.from_string("{{ s|wordcount }}")
        with pytest.raises(UndefinedError):
            t.render()

    def test_block(self, env):
        tmpl = env.from_string("{% filter lower|escape %}<HEHE>{% endfilter %}")
        assert tmpl.render() == "&lt;hehe&gt;"

    def test_chaining(self, env):
        tmpl = env.from_string("""{{ ['<foo>', '<bar>']|first|upper|escape }}""")
        assert tmpl.render() == "&lt;FOO&gt;"

    def test_sum(self, env):
        tmpl = env.from_string("""{{ [1, 2, 3, 4, 5, 6]|sum }}""")
        assert tmpl.render() == "21"

    def test_sum_attributes(self, env):
        tmpl = env.from_string("""{{ values|sum('value') }}""")
        assert tmpl.render(values=[{"value": 23}, {"value": 1}, {"value": 18}]) == "42"

    def test_sum_attributes_nested(self, env):
        tmpl = env.from_string("""{{ values|sum('real.value') }}""")
        assert (
            tmpl.render(
                values=[
                    {"real": {"value": 23}},
                    {"real": {"value": 1}},
                    {"real": {"value": 18}},
                ]
            )
            == "42"
        )

    def test_sum_attributes_tuple(self, env):
        tmpl = env.from_string("""{{ values.items()|sum('1') }}""")
        assert tmpl.render(values={"foo": 23, "bar": 1, "baz": 18}) == "42"

    def test_abs(self, env):
        tmpl = env.from_string("""{{ -1|abs }}|{{ 1|abs }}""")
        assert tmpl.render() == "1|1", tmpl.render()

    def test_round_positive(self, env):
        tmpl = env.from_string(
            "{{ 2.7|round }}|{{ 2.1|round }}|"
            "{{ 2.1234|round(3, 'floor') }}|"
            "{{ 2.1|round(0, 'ceil') }}"
        )
        assert tmpl.render() == "3.0|2.0|2.123|3.0", tmpl.render()

    def test_round_negative(self, env):
        tmpl = env.from_string(
            "{{ 21.3|round(-1)}}|"
            "{{ 21.3|round(-1, 'ceil')}}|"
            "{{ 21.3|round(-1, 'floor')}}"
        )
        assert tmpl.render() == "20.0|30.0|20.0", tmpl.render()

    def test_xmlattr(self, env):
        tmpl = env.from_string(
            "{{ {'foo': 42, 'bar': 23, 'fish': none, "
            "'spam': missing, 'blub:blub': '<?>'}|xmlattr }}"
        )
        out = tmpl.render().split()
        assert len(out) == 3
        assert 'foo="42"' in out
        assert 'bar="23"' in out
        assert 'blub:blub="&lt;?&gt;"' in out

    def test_sort1(self, env):
        tmpl = env.from_string("{{ [2, 3, 1]|sort }}|{{ [2, 3, 1]|sort(true) }}")
        assert tmpl.render() == "[1, 2, 3]|[3, 2, 1]"

    def test_sort2(self, env):
        tmpl = env.from_string('{{ "".join(["c", "A", "b", "D"]|sort) }}')
        assert tmpl.render() == "AbcD"

    def test_sort3(self, env):
        tmpl = env.from_string("""{{ ['foo', 'Bar', 'blah']|sort }}""")
        assert tmpl.render() == "['Bar', 'blah', 'foo']"

    def test_sort4(self, env):
        tmpl = env.from_string("""{{ items|sort(attribute='value')|join }}""")
        assert tmpl.render(items=map(Magic, [3, 2, 4, 1])) == "1234"

    def test_sort5(self, env):
        tmpl = env.from_string("""{{ items|sort(attribute='value.0')|join }}""")
        assert tmpl.render(items=map(Magic, [[3], [2], [4], [1]])) == "[1][2][3][4]"

    def test_sort6(self, env):
        tmpl = env.from_string("""{{ items|sort(attribute='value1,value2')|join }}""")
        assert (
            tmpl.render(
                items=map(
                    lambda x: Magic2(x[0], x[1]), [(3, 1), (2, 2), (2, 1), (2, 5)]
                )
            )
            == "(2,1)(2,2)(2,5)(3,1)"
        )

    def test_sort7(self, env):
        tmpl = env.from_string("""{{ items|sort(attribute='value2,value1')|join }}""")
        assert (
            tmpl.render(
                items=map(
                    lambda x: Magic2(x[0], x[1]), [(3, 1), (2, 2), (2, 1), (2, 5)]
                )
            )
            == "(2,1)(3,1)(2,2)(2,5)"
        )

    def test_sort8(self, env):
        tmpl = env.from_string(
            """{{ items|sort(attribute='value1.0,value2.0')|join }}"""
        )
        assert (
            tmpl.render(
                items=map(
                    lambda x: Magic2(x[0], x[1]),
                    [([3], [1]), ([2], [2]), ([2], [1]), ([2], [5])],
                )
            )
            == "([2],[1])([2],[2])([2],[5])([3],[1])"
        )

    def test_unique(self, env):
        t = env.from_string('{{ "".join(["b", "A", "a", "b"]|unique) }}')
        assert t.render() == "bA"

    def test_unique_case_sensitive(self, env):
        t = env.from_string('{{ "".join(["b", "A", "a", "b"]|unique(true)) }}')
        assert t.render() == "bAa"

    def test_unique_attribute(self, env):
        t = env.from_string("{{ items|unique(attribute='value')|join }}")
        assert t.render(items=map(Magic, [3, 2, 4, 1, 2])) == "3241"

    @pytest.mark.parametrize(
        "source,expect",
        (
            ('{{ ["a", "B"]|min }}', "a"),
            ('{{ ["a", "B"]|min(case_sensitive=true) }}', "B"),
            ("{{ []|min }}", ""),
            ('{{ ["a", "B"]|max }}', "B"),
            ('{{ ["a", "B"]|max(case_sensitive=true) }}', "a"),
            ("{{ []|max }}", ""),
        ),
    )
    def test_min_max(self, env, source, expect):
        t = env.from_string(source)
        assert t.render() == expect

    @pytest.mark.parametrize("name,expect", (("min", "1"), ("max", "9"),))
    def test_min_max_attribute(self, env, name, expect):
        t = env.from_string("{{ items|" + name + '(attribute="value") }}')
        assert t.render(items=map(Magic, [5, 1, 9])) == expect

    def test_groupby(self, env):
        tmpl = env.from_string(
            """
        {%- for grouper, list in [{'foo': 1, 'bar': 2},
                                  {'foo': 2, 'bar': 3},
                                  {'foo': 1, 'bar': 1},
                                  {'foo': 3, 'bar': 4}]|groupby('foo') -%}
            {{ grouper }}{% for x in list %}: {{ x.foo }}, {{ x.bar }}{% endfor %}|
        {%- endfor %}"""
        )
        assert tmpl.render().split("|") == ["1: 1, 2: 1, 1", "2: 2, 3", "3: 3, 4", ""]

    def test_groupby_tuple_index(self, env):
        tmpl = env.from_string(
            """
        {%- for grouper, list in [('a', 1), ('a', 2), ('b', 1)]|groupby(0) -%}
            {{ grouper }}{% for x in list %}:{{ x.1 }}{% endfor %}|
        {%- endfor %}"""
        )
        assert tmpl.render() == "a:1:2|b:1|"

    def test_groupby_multidot(self, env):
        Date = namedtuple("Date", "day,month,year")
        Article = namedtuple("Article", "title,date")
        articles = [
            Article("aha", Date(1, 1, 1970)),
            Article("interesting", Date(2, 1, 1970)),
            Article("really?", Date(3, 1, 1970)),
            Article("totally not", Date(1, 1, 1971)),
        ]
        tmpl = env.from_string(
            """
        {%- for year, list in articles|groupby('date.year') -%}
            {{ year }}{% for x in list %}[{{ x.title }}]{% endfor %}|
        {%- endfor %}"""
        )
        assert tmpl.render(articles=articles).split("|") == [
            "1970[aha][interesting][really?]",
            "1971[totally not]",
            "",
        ]

    def test_filtertag(self, env):
        tmpl = env.from_string(
            "{% filter upper|replace('FOO', 'foo') %}foobar{% endfilter %}"
        )
        assert tmpl.render() == "fooBAR"

    def test_replace(self, env):
        env = Environment()
        tmpl = env.from_string('{{ string|replace("o", 42) }}')
        assert tmpl.render(string="<foo>") == "<f4242>"
        env = Environment(autoescape=True)
        tmpl = env.from_string('{{ string|replace("o", 42) }}')
        assert tmpl.render(string="<foo>") == "&lt;f4242&gt;"
        tmpl = env.from_string('{{ string|replace("<", 42) }}')
        assert tmpl.render(string="<foo>") == "42foo&gt;"
        tmpl = env.from_string('{{ string|replace("o", ">x<") }}')
        assert tmpl.render(string=Markup("foo")) == "f&gt;x&lt;&gt;x&lt;"

    def test_forceescape(self, env):
        tmpl = env.from_string("{{ x|forceescape }}")
        assert tmpl.render(x=Markup("<div />")) == u"&lt;div /&gt;"

    def test_safe(self, env):
        env = Environment(autoescape=True)
        tmpl = env.from_string('{{ "<div>foo</div>"|safe }}')
        assert tmpl.render() == "<div>foo</div>"
        tmpl = env.from_string('{{ "<div>foo</div>" }}')
        assert tmpl.render() == "&lt;div&gt;foo&lt;/div&gt;"

    @pytest.mark.parametrize(
        ("value", "expect"),
        [
            ("Hello, world!", "Hello%2C%20world%21"),
            (u"Hello, world\u203d", "Hello%2C%20world%E2%80%BD"),
            ({"f": 1}, "f=1"),
            ([("f", 1), ("z", 2)], "f=1&amp;z=2"),
            ({u"\u203d": 1}, "%E2%80%BD=1"),
            ({0: 1}, "0=1"),
            ([("a b/c", "a b/c")], "a+b%2Fc=a+b%2Fc"),
            ("a b/c", "a%20b/c"),
        ],
    )
    def test_urlencode(self, value, expect):
        e = Environment(autoescape=True)
        t = e.from_string("{{ value|urlencode }}")
        assert t.render(value=value) == expect

    def test_simple_map(self, env):
        env = Environment()
        tmpl = env.from_string('{{ ["1", "2", "3"]|map("int")|sum }}')
        assert tmpl.render() == "6"

    def test_map_sum(self, env):
        tmpl = env.from_string('{{ [[1,2], [3], [4,5,6]]|map("sum")|list }}')
        assert tmpl.render() == "[3, 3, 15]"

    def test_attribute_map(self, env):
        User = namedtuple("User", "name")
        env = Environment()
        users = [
            User("john"),
            User("jane"),
            User("mike"),
        ]
        tmpl = env.from_string('{{ users|map(attribute="name")|join("|") }}')
        assert tmpl.render(users=users) == "john|jane|mike"

    def test_empty_map(self, env):
        env = Environment()
        tmpl = env.from_string('{{ none|map("upper")|list }}')
        assert tmpl.render() == "[]"

    def test_map_default(self, env):
        Fullname = namedtuple("Fullname", "firstname,lastname")
        Firstname = namedtuple("Firstname", "firstname")
        env = Environment()
        tmpl = env.from_string(
            '{{ users|map(attribute="lastname", default="smith")|join(", ") }}'
        )
        users = [
            Fullname("john", "lennon"),
            Fullname("jane", "edwards"),
            Fullname("jon", None),
            Firstname("mike"),
        ]
        assert tmpl.render(users=users) == "lennon, edwards, None, smith"

    def test_simple_select(self, env):
        env = Environment()
        tmpl = env.from_string('{{ [1, 2, 3, 4, 5]|select("odd")|join("|") }}')
        assert tmpl.render() == "1|3|5"

    def test_bool_select(self, env):
        env = Environment()
        tmpl = env.from_string('{{ [none, false, 0, 1, 2, 3, 4, 5]|select|join("|") }}')
        assert tmpl.render() == "1|2|3|4|5"

    def test_simple_reject(self, env):
        env = Environment()
        tmpl = env.from_string('{{ [1, 2, 3, 4, 5]|reject("odd")|join("|") }}')
        assert tmpl.render() == "2|4"

    def test_bool_reject(self, env):
        env = Environment()
        tmpl = env.from_string('{{ [none, false, 0, 1, 2, 3, 4, 5]|reject|join("|") }}')
        assert tmpl.render() == "None|False|0"

    def test_simple_select_attr(self, env):
        User = namedtuple("User", "name,is_active")
        env = Environment()
        users = [
            User("john", True),
            User("jane", True),
            User("mike", False),
        ]
        tmpl = env.from_string(
            '{{ users|selectattr("is_active")|map(attribute="name")|join("|") }}'
        )
        assert tmpl.render(users=users) == "john|jane"

    def test_simple_reject_attr(self, env):
        User = namedtuple("User", "name,is_active")
        env = Environment()
        users = [
            User("john", True),
            User("jane", True),
            User("mike", False),
        ]
        tmpl = env.from_string(
            '{{ users|rejectattr("is_active")|map(attribute="name")|join("|") }}'
        )
        assert tmpl.render(users=users) == "mike"

    def test_func_select_attr(self, env):
        User = namedtuple("User", "id,name")
        env = Environment()
        users = [
            User(1, "john"),
            User(2, "jane"),
            User(3, "mike"),
        ]
        tmpl = env.from_string(
            '{{ users|selectattr("id", "odd")|map(attribute="name")|join("|") }}'
        )
        assert tmpl.render(users=users) == "john|mike"

    def test_func_reject_attr(self, env):
        User = namedtuple("User", "id,name")
        env = Environment()
        users = [
            User(1, "john"),
            User(2, "jane"),
            User(3, "mike"),
        ]
        tmpl = env.from_string(
            '{{ users|rejectattr("id", "odd")|map(attribute="name")|join("|") }}'
        )
        assert tmpl.render(users=users) == "jane"

    def test_json_dump(self):
        env = Environment(autoescape=True)
        t = env.from_string("{{ x|tojson }}")
        assert t.render(x={"foo": "bar"}) == '{"foo": "bar"}'
        assert t.render(x="\"ba&r'") == r'"\"ba\u0026r\u0027"'
        assert t.render(x="<bar>") == r'"\u003cbar\u003e"'

        def my_dumps(value, **options):
            assert options == {"foo": "bar"}
            return "42"

        env.policies["json.dumps_function"] = my_dumps
        env.policies["json.dumps_kwargs"] = {"foo": "bar"}
        assert t.render(x=23) == "42"

    def test_wordwrap(self, env):
        env.newline_sequence = "\n"
        t = env.from_string("{{ s|wordwrap(20) }}")
        result = t.render(s="Hello!\nThis is Jinja saying something.")
        assert result == "Hello!\nThis is Jinja saying\nsomething."
