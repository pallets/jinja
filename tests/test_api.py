import shutil
import tempfile
from pathlib import Path

import pytest

from jinja2 import ChainableUndefined
from jinja2 import DebugUndefined
from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import is_undefined
from jinja2 import make_logging_undefined
from jinja2 import meta
from jinja2 import StrictUndefined
from jinja2 import Template
from jinja2 import TemplatesNotFound
from jinja2 import Undefined
from jinja2 import UndefinedError
from jinja2.compiler import CodeGenerator
from jinja2.runtime import Context
from jinja2.utils import Cycler
from jinja2.utils import pass_context
from jinja2.utils import pass_environment
from jinja2.utils import pass_eval_context


class TestExtendedAPI:
    def test_item_and_attribute(self, env):
        from jinja2.sandbox import SandboxedEnvironment

        for env in Environment(), SandboxedEnvironment():
            tmpl = env.from_string("{{ foo.items()|list }}")
            assert tmpl.render(foo={"items": 42}) == "[('items', 42)]"
            tmpl = env.from_string('{{ foo|attr("items")()|list }}')
            assert tmpl.render(foo={"items": 42}) == "[('items', 42)]"
            tmpl = env.from_string('{{ foo["items"] }}')
            assert tmpl.render(foo={"items": 42}) == "42"

    def test_finalize(self):
        e = Environment(finalize=lambda v: "" if v is None else v)
        t = e.from_string("{% for item in seq %}|{{ item }}{% endfor %}")
        assert t.render(seq=(None, 1, "foo")) == "||1|foo"

    def test_finalize_constant_expression(self):
        e = Environment(finalize=lambda v: "" if v is None else v)
        t = e.from_string("<{{ none }}>")
        assert t.render() == "<>"

    def test_no_finalize_template_data(self):
        e = Environment(finalize=lambda v: type(v).__name__)
        t = e.from_string("<{{ value }}>")
        # If template data was finalized, it would print "strintstr".
        assert t.render(value=123) == "<int>"

    def test_context_finalize(self):
        @pass_context
        def finalize(context, value):
            return value * context["scale"]

        e = Environment(finalize=finalize)
        t = e.from_string("{{ value }}")
        assert t.render(value=5, scale=3) == "15"

    def test_eval_finalize(self):
        @pass_eval_context
        def finalize(eval_ctx, value):
            return str(eval_ctx.autoescape) + value

        e = Environment(finalize=finalize, autoescape=True)
        t = e.from_string("{{ value }}")
        assert t.render(value="<script>") == "True&lt;script&gt;"

    def test_env_autoescape(self):
        @pass_environment
        def finalize(env, value):
            return " ".join(
                (env.variable_start_string, repr(value), env.variable_end_string)
            )

        e = Environment(finalize=finalize)
        t = e.from_string("{{ value }}")
        assert t.render(value="hello") == "{{ 'hello' }}"

    def test_cycler(self, env):
        items = 1, 2, 3
        c = Cycler(*items)
        for item in items + items:
            assert c.current == item
            assert next(c) == item
        next(c)
        assert c.current == 2
        c.reset()
        assert c.current == 1

    def test_expressions(self, env):
        expr = env.compile_expression("foo")
        assert expr() is None
        assert expr(foo=42) == 42
        expr2 = env.compile_expression("foo", undefined_to_none=False)
        assert is_undefined(expr2())

        expr = env.compile_expression("42 + foo")
        assert expr(foo=42) == 84

    def test_template_passthrough(self, env):
        t = Template("Content")
        assert env.get_template(t) is t
        assert env.select_template([t]) is t
        assert env.get_or_select_template([t]) is t
        assert env.get_or_select_template(t) is t

    def test_get_template_undefined(self, env):
        """Passing Undefined to get/select_template raises an
        UndefinedError or shows the undefined message in the list.
        """
        env.loader = DictLoader({})
        t = Undefined(name="no_name_1")

        with pytest.raises(UndefinedError):
            env.get_template(t)

        with pytest.raises(UndefinedError):
            env.get_or_select_template(t)

        with pytest.raises(UndefinedError):
            env.select_template(t)

        with pytest.raises(TemplatesNotFound) as exc_info:
            env.select_template([t, "no_name_2"])

        exc_message = str(exc_info.value)
        assert "'no_name_1' is undefined" in exc_message
        assert "no_name_2" in exc_message

    def test_autoescape_autoselect(self, env):
        def select_autoescape(name):
            if name is None or "." not in name:
                return False
            return name.endswith(".html")

        env = Environment(
            autoescape=select_autoescape,
            loader=DictLoader({"test.txt": "{{ foo }}", "test.html": "{{ foo }}"}),
        )
        t = env.get_template("test.txt")
        assert t.render(foo="<foo>") == "<foo>"
        t = env.get_template("test.html")
        assert t.render(foo="<foo>") == "&lt;foo&gt;"
        t = env.from_string("{{ foo }}")
        assert t.render(foo="<foo>") == "<foo>"

    def test_sandbox_max_range(self, env):
        from jinja2.sandbox import SandboxedEnvironment, MAX_RANGE

        env = SandboxedEnvironment()
        t = env.from_string("{% for item in range(total) %}{{ item }}{% endfor %}")

        with pytest.raises(OverflowError):
            t.render(total=MAX_RANGE + 1)


class TestMeta:
    def test_find_undeclared_variables(self, env):
        ast = env.parse("{% set foo = 42 %}{{ bar + foo }}")
        x = meta.find_undeclared_variables(ast)
        assert x == {"bar"}

        ast = env.parse(
            "{% set foo = 42 %}{{ bar + foo }}"
            "{% macro meh(x) %}{{ x }}{% endmacro %}"
            "{% for item in seq %}{{ muh(item) + meh(seq) }}"
            "{% endfor %}"
        )
        x = meta.find_undeclared_variables(ast)
        assert x == {"bar", "seq", "muh"}

        ast = env.parse("{% for x in range(5) %}{{ x }}{% endfor %}{{ foo }}")
        x = meta.find_undeclared_variables(ast)
        assert x == {"foo"}

    def test_find_refererenced_templates(self, env):
        ast = env.parse('{% extends "layout.html" %}{% include helper %}')
        i = meta.find_referenced_templates(ast)
        assert next(i) == "layout.html"
        assert next(i) is None
        assert list(i) == []

        ast = env.parse(
            '{% extends "layout.html" %}'
            '{% from "test.html" import a, b as c %}'
            '{% import "meh.html" as meh %}'
            '{% include "muh.html" %}'
        )
        i = meta.find_referenced_templates(ast)
        assert list(i) == ["layout.html", "test.html", "meh.html", "muh.html"]

    def test_find_included_templates(self, env):
        ast = env.parse('{% include ["foo.html", "bar.html"] %}')
        i = meta.find_referenced_templates(ast)
        assert list(i) == ["foo.html", "bar.html"]

        ast = env.parse('{% include ("foo.html", "bar.html") %}')
        i = meta.find_referenced_templates(ast)
        assert list(i) == ["foo.html", "bar.html"]

        ast = env.parse('{% include ["foo.html", "bar.html", foo] %}')
        i = meta.find_referenced_templates(ast)
        assert list(i) == ["foo.html", "bar.html", None]

        ast = env.parse('{% include ("foo.html", "bar.html", foo) %}')
        i = meta.find_referenced_templates(ast)
        assert list(i) == ["foo.html", "bar.html", None]


class TestStreaming:
    def test_basic_streaming(self, env):
        t = env.from_string(
            "<ul>{% for item in seq %}<li>{{ loop.index }} - {{ item }}</li>"
            "{%- endfor %}</ul>"
        )
        stream = t.stream(seq=list(range(3)))
        assert next(stream) == "<ul>"
        assert "".join(stream) == "<li>1 - 0</li><li>2 - 1</li><li>3 - 2</li></ul>"

    def test_buffered_streaming(self, env):
        tmpl = env.from_string(
            "<ul>{% for item in seq %}<li>{{ loop.index }} - {{ item }}</li>"
            "{%- endfor %}</ul>"
        )
        stream = tmpl.stream(seq=list(range(3)))
        stream.enable_buffering(size=3)
        assert next(stream) == "<ul><li>1"
        assert next(stream) == " - 0</li>"

    def test_streaming_behavior(self, env):
        tmpl = env.from_string("")
        stream = tmpl.stream()
        assert not stream.buffered
        stream.enable_buffering(20)
        assert stream.buffered
        stream.disable_buffering()
        assert not stream.buffered

    def test_dump_stream(self, env):
        tmp = Path(tempfile.mkdtemp())
        try:
            tmpl = env.from_string("\u2713")
            stream = tmpl.stream()
            stream.dump(str(tmp / "dump.txt"), "utf-8")
            assert (tmp / "dump.txt").read_bytes() == b"\xe2\x9c\x93"
        finally:
            shutil.rmtree(tmp)


class TestUndefined:
    def test_stopiteration_is_undefined(self):
        def test():
            raise StopIteration()

        t = Template("A{{ test() }}B")
        assert t.render(test=test) == "AB"
        t = Template("A{{ test().missingattribute }}B")
        pytest.raises(UndefinedError, t.render, test=test)

    def test_undefined_and_special_attributes(self):
        with pytest.raises(AttributeError):
            Undefined("Foo").__dict__

    def test_undefined_attribute_error(self):
        # Django's LazyObject turns the __class__ attribute into a
        # property that resolves the wrapped function. If that wrapped
        # function raises an AttributeError, printing the repr of the
        # object in the undefined message would cause a RecursionError.
        class Error:
            @property  # type: ignore
            def __class__(self):
                raise AttributeError()

        u = Undefined(obj=Error(), name="hello")

        with pytest.raises(UndefinedError):
            getattr(u, "recursion", None)

    def test_logging_undefined(self):
        _messages = []

        class DebugLogger:
            def warning(self, msg, *args):
                _messages.append("W:" + msg % args)

            def error(self, msg, *args):
                _messages.append("E:" + msg % args)

        logging_undefined = make_logging_undefined(DebugLogger())
        env = Environment(undefined=logging_undefined)
        assert env.from_string("{{ missing }}").render() == ""
        pytest.raises(UndefinedError, env.from_string("{{ missing.attribute }}").render)
        assert env.from_string("{{ missing|list }}").render() == "[]"
        assert env.from_string("{{ missing is not defined }}").render() == "True"
        assert env.from_string("{{ foo.missing }}").render(foo=42) == ""
        assert env.from_string("{{ not missing }}").render() == "True"
        assert _messages == [
            "W:Template variable warning: 'missing' is undefined",
            "E:Template variable error: 'missing' is undefined",
            "W:Template variable warning: 'missing' is undefined",
            "W:Template variable warning: 'int object' has no attribute 'missing'",
            "W:Template variable warning: 'missing' is undefined",
        ]

    def test_default_undefined(self):
        env = Environment(undefined=Undefined)
        assert env.from_string("{{ missing }}").render() == ""
        pytest.raises(UndefinedError, env.from_string("{{ missing.attribute }}").render)
        assert env.from_string("{{ missing|list }}").render() == "[]"
        assert env.from_string("{{ missing is not defined }}").render() == "True"
        assert env.from_string("{{ foo.missing }}").render(foo=42) == ""
        assert env.from_string("{{ not missing }}").render() == "True"
        pytest.raises(UndefinedError, env.from_string("{{ missing - 1}}").render)
        assert env.from_string("{{ 'foo' in missing }}").render() == "False"
        und1 = Undefined(name="x")
        und2 = Undefined(name="y")
        assert und1 == und2
        assert und1 != 42
        assert hash(und1) == hash(und2) == hash(Undefined())
        with pytest.raises(AttributeError):
            getattr(Undefined, "__slots__")  # noqa: B009

    def test_chainable_undefined(self):
        env = Environment(undefined=ChainableUndefined)
        # The following tests are copied from test_default_undefined
        assert env.from_string("{{ missing }}").render() == ""
        assert env.from_string("{{ missing|list }}").render() == "[]"
        assert env.from_string("{{ missing is not defined }}").render() == "True"
        assert env.from_string("{{ foo.missing }}").render(foo=42) == ""
        assert env.from_string("{{ not missing }}").render() == "True"
        pytest.raises(UndefinedError, env.from_string("{{ missing - 1}}").render)
        with pytest.raises(AttributeError):
            getattr(ChainableUndefined, "__slots__")  # noqa: B009

        # The following tests ensure subclass functionality works as expected
        assert env.from_string('{{ missing.bar["baz"] }}').render() == ""
        assert env.from_string('{{ foo.bar["baz"]._undefined_name }}').render() == "foo"
        assert (
            env.from_string('{{ foo.bar["baz"]._undefined_name }}').render(foo=42)
            == "bar"
        )
        assert (
            env.from_string('{{ foo.bar["baz"]._undefined_name }}').render(
                foo={"bar": 42}
            )
            == "baz"
        )

    def test_debug_undefined(self):
        env = Environment(undefined=DebugUndefined)
        assert env.from_string("{{ missing }}").render() == "{{ missing }}"
        pytest.raises(UndefinedError, env.from_string("{{ missing.attribute }}").render)
        assert env.from_string("{{ missing|list }}").render() == "[]"
        assert env.from_string("{{ missing is not defined }}").render() == "True"
        assert (
            env.from_string("{{ foo.missing }}").render(foo=42)
            == "{{ no such element: int object['missing'] }}"
        )
        assert env.from_string("{{ not missing }}").render() == "True"
        undefined_hint = "this is testing undefined hint of DebugUndefined"
        assert (
            str(DebugUndefined(hint=undefined_hint))
            == f"{{{{ undefined value printed: {undefined_hint} }}}}"
        )
        with pytest.raises(AttributeError):
            getattr(DebugUndefined, "__slots__")  # noqa: B009

    def test_strict_undefined(self):
        env = Environment(undefined=StrictUndefined)
        pytest.raises(UndefinedError, env.from_string("{{ missing }}").render)
        pytest.raises(UndefinedError, env.from_string("{{ missing.attribute }}").render)
        pytest.raises(UndefinedError, env.from_string("{{ missing|list }}").render)
        pytest.raises(UndefinedError, env.from_string("{{ 'foo' in missing }}").render)
        assert env.from_string("{{ missing is not defined }}").render() == "True"
        pytest.raises(
            UndefinedError, env.from_string("{{ foo.missing }}").render, foo=42
        )
        pytest.raises(UndefinedError, env.from_string("{{ not missing }}").render)
        assert (
            env.from_string('{{ missing|default("default", true) }}').render()
            == "default"
        )
        with pytest.raises(AttributeError):
            getattr(StrictUndefined, "__slots__")  # noqa: B009
        assert env.from_string('{{ "foo" if false }}').render() == ""

    def test_indexing_gives_undefined(self):
        t = Template("{{ var[42].foo }}")
        pytest.raises(UndefinedError, t.render, var=0)

    def test_none_gives_proper_error(self):
        with pytest.raises(UndefinedError, match="'None' has no attribute 'split'"):
            Environment().getattr(None, "split")()

    def test_object_repr(self):
        with pytest.raises(
            UndefinedError, match="'int object' has no attribute 'upper'"
        ):
            Undefined(obj=42, name="upper")()


class TestLowLevel:
    def test_custom_code_generator(self):
        class CustomCodeGenerator(CodeGenerator):
            def visit_Const(self, node, frame=None):
                # This method is pure nonsense, but works fine for testing...
                if node.value == "foo":
                    self.write(repr("bar"))
                else:
                    super().visit_Const(node, frame)

        class CustomEnvironment(Environment):
            code_generator_class = CustomCodeGenerator

        env = CustomEnvironment()
        tmpl = env.from_string('{% set foo = "foo" %}{{ foo }}')
        assert tmpl.render() == "bar"

    def test_custom_context(self):
        class CustomContext(Context):
            def resolve_or_missing(self, key):
                return "resolve-" + key

        class CustomEnvironment(Environment):
            context_class = CustomContext

        env = CustomEnvironment()
        tmpl = env.from_string("{{ foo }}")
        assert tmpl.render() == "resolve-foo"
