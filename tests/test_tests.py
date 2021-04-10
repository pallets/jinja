import pytest
from markupsafe import Markup

from jinja2 import Environment
from jinja2 import TemplateAssertionError
from jinja2 import TemplateRuntimeError


class MyDict(dict):
    pass


class TestTestsCase:
    def test_defined(self, env):
        tmpl = env.from_string("{{ missing is defined }}|{{ true is defined }}")
        assert tmpl.render() == "False|True"

    def test_even(self, env):
        tmpl = env.from_string("""{{ 1 is even }}|{{ 2 is even }}""")
        assert tmpl.render() == "False|True"

    def test_odd(self, env):
        tmpl = env.from_string("""{{ 1 is odd }}|{{ 2 is odd }}""")
        assert tmpl.render() == "True|False"

    def test_lower(self, env):
        tmpl = env.from_string("""{{ "foo" is lower }}|{{ "FOO" is lower }}""")
        assert tmpl.render() == "True|False"

    # Test type checks
    @pytest.mark.parametrize(
        "op,expect",
        (
            ("none is none", True),
            ("false is none", False),
            ("true is none", False),
            ("42 is none", False),
            ("none is true", False),
            ("false is true", False),
            ("true is true", True),
            ("0 is true", False),
            ("1 is true", False),
            ("42 is true", False),
            ("none is false", False),
            ("false is false", True),
            ("true is false", False),
            ("0 is false", False),
            ("1 is false", False),
            ("42 is false", False),
            ("none is boolean", False),
            ("false is boolean", True),
            ("true is boolean", True),
            ("0 is boolean", False),
            ("1 is boolean", False),
            ("42 is boolean", False),
            ("0.0 is boolean", False),
            ("1.0 is boolean", False),
            ("3.14159 is boolean", False),
            ("none is integer", False),
            ("false is integer", False),
            ("true is integer", False),
            ("42 is integer", True),
            ("3.14159 is integer", False),
            ("(10 ** 100) is integer", True),
            ("none is float", False),
            ("false is float", False),
            ("true is float", False),
            ("42 is float", False),
            ("4.2 is float", True),
            ("(10 ** 100) is float", False),
            ("none is number", False),
            ("false is number", True),
            ("true is number", True),
            ("42 is number", True),
            ("3.14159 is number", True),
            ("complex is number", True),
            ("(10 ** 100) is number", True),
            ("none is string", False),
            ("false is string", False),
            ("true is string", False),
            ("42 is string", False),
            ('"foo" is string', True),
            ("none is sequence", False),
            ("false is sequence", False),
            ("42 is sequence", False),
            ('"foo" is sequence', True),
            ("[] is sequence", True),
            ("[1, 2, 3] is sequence", True),
            ("{} is sequence", True),
            ("none is mapping", False),
            ("false is mapping", False),
            ("42 is mapping", False),
            ('"foo" is mapping', False),
            ("[] is mapping", False),
            ("{} is mapping", True),
            ("mydict is mapping", True),
            ("none is iterable", False),
            ("false is iterable", False),
            ("42 is iterable", False),
            ('"foo" is iterable', True),
            ("[] is iterable", True),
            ("{} is iterable", True),
            ("range(5) is iterable", True),
            ("none is callable", False),
            ("false is callable", False),
            ("42 is callable", False),
            ('"foo" is callable', False),
            ("[] is callable", False),
            ("{} is callable", False),
            ("range is callable", True),
        ),
    )
    def test_types(self, env, op, expect):
        t = env.from_string(f"{{{{ {op} }}}}")
        assert t.render(mydict=MyDict(), complex=complex(1, 2)) == str(expect)

    def test_upper(self, env):
        tmpl = env.from_string('{{ "FOO" is upper }}|{{ "foo" is upper }}')
        assert tmpl.render() == "True|False"

    def test_equalto(self, env):
        tmpl = env.from_string(
            "{{ foo is eq 12 }}|"
            "{{ foo is eq 0 }}|"
            "{{ foo is eq (3 * 4) }}|"
            '{{ bar is eq "baz" }}|'
            '{{ bar is eq "zab" }}|'
            '{{ bar is eq ("ba" + "z") }}|'
            "{{ bar is eq bar }}|"
            "{{ bar is eq foo }}"
        )
        assert (
            tmpl.render(foo=12, bar="baz")
            == "True|False|True|True|False|True|True|False"
        )

    @pytest.mark.parametrize(
        "op,expect",
        (
            ("eq 2", True),
            ("eq 3", False),
            ("ne 3", True),
            ("ne 2", False),
            ("lt 3", True),
            ("lt 2", False),
            ("le 2", True),
            ("le 1", False),
            ("gt 1", True),
            ("gt 2", False),
            ("ge 2", True),
            ("ge 3", False),
        ),
    )
    def test_compare_aliases(self, env, op, expect):
        t = env.from_string(f"{{{{ 2 is {op} }}}}")
        assert t.render() == str(expect)

    def test_sameas(self, env):
        tmpl = env.from_string("{{ foo is sameas false }}|{{ 0 is sameas false }}")
        assert tmpl.render(foo=False) == "True|False"

    def test_no_paren_for_arg1(self, env):
        tmpl = env.from_string("{{ foo is sameas none }}")
        assert tmpl.render(foo=None) == "True"

    def test_escaped(self, env):
        env = Environment(autoescape=True)
        tmpl = env.from_string("{{ x is escaped }}|{{ y is escaped }}")
        assert tmpl.render(x="foo", y=Markup("foo")) == "False|True"

    def test_greaterthan(self, env):
        tmpl = env.from_string("{{ 1 is greaterthan 0 }}|{{ 0 is greaterthan 1 }}")
        assert tmpl.render() == "True|False"

    def test_lessthan(self, env):
        tmpl = env.from_string("{{ 0 is lessthan 1 }}|{{ 1 is lessthan 0 }}")
        assert tmpl.render() == "True|False"

    def test_multiple_tests(self):
        items = []

        def matching(x, y):
            items.append((x, y))
            return False

        env = Environment()
        env.tests["matching"] = matching
        tmpl = env.from_string(
            "{{ 'us-west-1' is matching '(us-east-1|ap-northeast-1)'"
            " or 'stage' is matching '(dev|stage)' }}"
        )
        assert tmpl.render() == "False"
        assert items == [
            ("us-west-1", "(us-east-1|ap-northeast-1)"),
            ("stage", "(dev|stage)"),
        ]

    def test_in(self, env):
        tmpl = env.from_string(
            '{{ "o" is in "foo" }}|'
            '{{ "foo" is in "foo" }}|'
            '{{ "b" is in "foo" }}|'
            "{{ 1 is in ((1, 2)) }}|"
            "{{ 3 is in ((1, 2)) }}|"
            "{{ 1 is in [1, 2] }}|"
            "{{ 3 is in [1, 2] }}|"
            '{{ "foo" is in {"foo": 1}}}|'
            '{{ "baz" is in {"bar": 1}}}'
        )
        assert tmpl.render() == "True|True|False|True|False|True|False|True|False"


def test_name_undefined(env):
    with pytest.raises(TemplateAssertionError, match="No test named 'f'"):
        env.from_string("{{ x is f }}")


def test_name_undefined_in_if(env):
    t = env.from_string("{% if x is defined %}{{ x is f }}{% endif %}")
    assert t.render() == ""

    with pytest.raises(TemplateRuntimeError, match="No test named 'f'"):
        t.render(x=1)


def test_is_filter(env):
    assert env.call_test("filter", "title")
    assert not env.call_test("filter", "bad-name")


def test_is_test(env):
    assert env.call_test("test", "number")
    assert not env.call_test("test", "bad-name")
