import pytest

from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import select_autoescape
from jinja2.exceptions import TemplateConfigurationError
from jinja2.utils import get_wrapped_escape_class


def custom_escape(s):
    return str(s).replace("$", "€")


@pytest.fixture()
def escape_special_extensions():
    def star(s):
        return str(s).replace("*", "star")

    def tilde(s):
        return str(s).replace("~", "tilde")

    def plus(s):
        return str(s).replace("+", "plus")

    return {"star": star, "tilde": tilde, "plus": plus, "foo": star}


class TestCustomAutoescape:
    def test_custom_join(self, env_custom_autoescape):
        from jinja2.nodes import EvalContext

        ctx = EvalContext(env_custom_autoescape)
        escape = ctx.get_escape_function()
        combine = ["$foo", escape("$bar"), ctx.mark_safe("$dollar")]
        assert ctx.mark_safe("").join(combine) == "€foo€bar$dollar"
        # Make sure the result was really marked as escaped
        assert escape(ctx.mark_safe("").join(combine)) == "€foo€bar$dollar"

    def test_non_custom_modulo(self, env):
        from jinja2.nodes import EvalContext

        ctx = EvalContext(env)
        escape = ctx.get_escape_function()
        source = ctx.mark_safe("%s,%s,%s")
        target = ("$foo", escape("$bar"), ctx.mark_safe("$dollar"))
        assert source % target == "$foo,$bar,$dollar"
        # Make sure the result was marked as escaped
        assert escape(source % target) == "$foo,$bar,$dollar"

    def test_eval_context(self, env_custom_autoescape):
        t = env_custom_autoescape.from_string(
            "{% autoescape true %}|{{ foo }}|{% endautoescape %}"
        )
        assert t.render(foo="bar$>") == "|bar€>|"
        t = env_custom_autoescape.from_string(
            "{% autoescape false %}|{{ foo }}|{% endautoescape %}"
        )
        assert t.render(foo="bar$>") == "|bar$>|"

    def test_custom_modulo(self, env_custom_autoescape):
        from jinja2.nodes import EvalContext

        ctx = EvalContext(env_custom_autoescape)
        escape = ctx.get_escape_function()
        source = ctx.mark_safe("%s,%s,%s")
        target = ("$foo", escape("$bar"), ctx.mark_safe("$dollar"))
        assert source % target == "€foo,€bar,$dollar"
        # Make sure the result is marked as escaped
        assert escape(source % target) == "€foo,€bar,$dollar"

    def test_default_escape(self):
        env = Environment(autoescape=True)
        t = env.from_string("{{ foo|safe }}")
        assert t.render(foo="<$FOO$>") == "<$FOO$>"

    def test_default_escape_custom(self, env_custom_autoescape):
        env = env_custom_autoescape
        t = env.from_string("{{ foo|safe }}")
        assert t.render(foo="<$FOO$>") == "<$FOO$>"

    @pytest.mark.parametrize(
        "escape_function", [custom_escape, get_wrapped_escape_class(custom_escape)]
    )
    def test_custom_markup_environment_autoescape(self, escape_function):
        env = Environment(default_escape=escape_function, autoescape=True)
        t = env.from_string("{{ foo }}")
        assert t.render(foo="100$") == "100€"
        t = env.from_string("{{ foo|e }}")
        assert t.render(foo="100$") == "100€"
        t = env.from_string("{{ foo|escape }}")
        assert t.render(foo="100$") == "100€"
        t = env.from_string("{{ foo|safe }}")
        assert t.render(foo="100$") == "100$"
        t = env.from_string("{{ foo|safe|escape }}")
        assert t.render(foo="100$") == "100$"

    @pytest.mark.parametrize(
        "escape_function", [custom_escape, get_wrapped_escape_class(custom_escape)]
    )
    def test_custom_markup_environment_manual_escape(self, escape_function):
        env = Environment(default_escape=escape_function)
        t = env.from_string("{{ foo|e }}")
        assert t.render(foo="100$") == "100€"
        t = env.from_string("{{ foo|escape }}")
        assert t.render(foo="100$") == "100€"
        t = env.from_string("{{ foo|safe }}")
        assert t.render(foo="100$") == "100$"
        t = env.from_string("{{ foo|safe|escape }}")
        assert t.render(foo="100$") == "100$"

    def test_do_join_custom_volatile(self, custom_escape_func):
        env = Environment(
            extensions=["jinja2.ext.do"],
            default_escape=custom_escape_func,
        )
        tmpl = env.from_string(
            """
            {% autoescape True %}
            {%- set items = [] %}
            {%- for char in "foo>$" %}
                {%- do items.append(loop.index0 ~ char) %}
            {%- endfor %}{{ items|join(', ') }}
            {% endautoescape %}"""
        )
        assert tmpl.render().strip() == "0f, 1o, 2o, 3>, 4€"

    def test_do_join_custom_autoescape(self, custom_escape_func):
        env = Environment(
            extensions=["jinja2.ext.do"], autoescape=lambda x: custom_escape_func
        )
        tmpl = env.from_string(
            """
            {%- set items = [] %}
            {%- for char in "foo>$" %}
                {%- do items.append(loop.index0 ~ char) %}
            {%- endfor %}{{ items|join(', ') }}"""
        )
        assert tmpl.render() == "0f, 1o, 2o, 3>, 4€"

    def test_mixed_files_include(self, escape_special_extensions):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(
                special_extensions=escape_special_extensions,
                enabled_extensions=["htm", "html"],
                disabled_extensions=["txt"],
            ),
            loader=DictLoader(
                {
                    "disable.txt": "{{ foo }};{% include 'inc.tilde' %};",
                    "main.star": "{{ foo }};{% include 'inc.tilde' %};",
                    "main_disable.star": "{{ foo }};{% include 'disable.txt' %};",
                    "inc.tilde": "{{ foo }};{% include 'simple.plus' %};",
                    "simple.htm": "{{ foo }}",
                    "simple.plus": "{{ foo }}",
                    "simple.star": "{{ foo }}",
                    "simple.tilde": "{{ foo }}",
                    "main_html.star": "{{ foo }};{% include 'inc_html.tilde' %};",
                    "inc_html.tilde": "{{ foo }};{% include 'inc.html' %};",
                    "inc.html": "{{ foo }};{% include 'inc.txt' %};",
                    "inc.txt": "{{ foo }};{% include 'simple.plus' %};",
                }
            ),
        )
        # First test simple stuff
        t = env.get_template("simple.plus")
        assert t.render(foo=chars) == "<*~plus>"
        t = env.get_template("simple.star")
        assert t.render(foo=chars) == "<star~+>"
        t = env.get_template("simple.tilde")
        assert t.render(foo=chars) == "<*tilde+>"
        t = env.get_template("simple.htm")
        assert t.render(foo=chars) == "&lt;*~+&gt;"
        t = env.get_template("inc.tilde")
        assert t.render(foo=chars) == "<*tilde+>;<*~plus>;"
        t = env.get_template("main.star")
        assert t.render(foo=chars) == "<star~+>;<*tilde+>;<*~plus>;;"
        t = env.get_template("disable.txt")
        assert t.render(foo=chars) == "<*~+>;<*tilde+>;<*~plus>;;"
        t = env.get_template("main_disable.star")
        assert t.render(foo=chars) == "<star~+>;<*~+>;<*tilde+>;<*~plus>;;;"
        t = env.get_template("main_html.star")
        assert (
            t.render(foo=chars) == "<star~+>;<*tilde+>;&lt;*~+&gt;;<*~+>;<*~plus>;;;;"
        )

    def test_mixed_files_include_plus_extend_with_block(
        self, escape_special_extensions
    ):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(
                special_extensions=escape_special_extensions,
                enabled_extensions=["htm", "html"],
                disabled_extensions=["txt"],
            ),
            loader=DictLoader(
                {
                    "main.star": "StarMain{{ foo }};{% include 'inc.tilde' %};",
                    "inc.plus": (
                        "PlusMain{{ foo }};"
                        "{% block body %}"
                        "PlusBody{{ foo }};"
                        "{% endblock %}"
                    ),
                    "inc.tilde": (
                        "{% extends 'inc.plus' %}"
                        "TildeMain{{ foo }};"
                        "{% block body %}"
                        "MainBody{{ foo }};"
                        "{{ super() }}"
                        "{% endblock %}"
                    ),
                }
            ),
            allow_mixed_escape_extends=True,
        )
        t = env.get_template("main.star")
        # This is not 100% what is expected, that is why we throw an
        # exception by default. We documented this behavior, so even
        # you can fix it, changing it should be considered a breaking
        # change
        assert t.render(foo=chars) == (
            "StarMain<star~+>;"
            "PlusMain<*tilde+>;"
            "MainBody<*tilde+>;"
            "PlusBody<*tilde+>;;"
        )

    def test_mixed_files_extend(self, escape_special_extensions):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(
                {
                    "main.star": "{% block body %}{{ foo }};{% endblock %}",
                    "inc.star": (
                        "{% extends 'main.star' %}"
                        "{% block body %}{{ super() }}{{ foo }};{% endblock %}"
                    ),
                    "inc.tilde": (
                        "{% extends 'main.star' %}"
                        "{% block body %}{{ super() }}{{ foo }};{% endblock %}"
                    ),
                }
            ),
            allow_mixed_escape_extends=True,
        )
        # First test simple stuff
        t = env.get_template("main.star")
        assert t.render(foo=chars) == "<star~+>;"

        t = env.get_template("inc.star")
        assert t.render(foo=chars) == "<star~+>;<star~+>;"

        t = env.get_template("inc.tilde")
        # This is not 100% what is expected, that is why we throw an
        # exception by default. We documented this behavior, so even
        # you can fix it, changing it should be considered a breaking
        # change
        assert t.render(foo=chars) == "<*tilde+>;<*tilde+>;"

    def test_mixed_files_extend_same_function(self, escape_special_extensions):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(
                {
                    "main.star": "{% block body %}{{ foo }};{% endblock %}",
                    "inc.star": (
                        "{% extends 'main.star' %}"
                        "{% block body %}{{ super() }}{{ foo }};{% endblock %}"
                    ),
                    "inc.foo": (
                        "{% extends 'inc.star' %}"
                        "{% block body %}{{ super() }}{{ foo }};{% endblock %}"
                    ),
                }
            ),
            allow_mixed_escape_extends=True,
        )
        # First test simple stuff
        t = env.get_template("main.star")
        assert t.render(foo=chars) == "<star~+>;"

        t = env.get_template("inc.star")
        assert t.render(foo=chars) == "<star~+>;<star~+>;"

        t = env.get_template("inc.foo")
        assert t.render(foo=chars) == "<star~+>;<star~+>;<star~+>;"

    def test_mixed_files_extends_with_macro(self, escape_special_extensions):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(
                {
                    "macro.star": (
                        "{% macro bar() -%}bar{{ foo }}{%- endmacro %}"
                        "{% block body %}{{ foo }};{{ bar() }}{% endblock %}"
                    ),
                    "inc.plus": (
                        "{% extends 'macro.star' %}"
                        "{% block body %}"
                        "{{ super() }}{{ foo }};{{ bar () }}"
                        "{% endblock %}"
                    ),
                }
            ),
            allow_mixed_escape_extends=True,
        )
        # First test simple stuff
        t = env.get_template("macro.star")
        assert t.render(foo=chars) == "<star~+>;bar<star~+>"
        t = env.get_template("inc.plus")
        # This is not 100% what is expected, that is why we throw an
        # exception by default. We documented this behavior, so even
        # you can fix it, changing it should be considered a breaking
        # change
        assert t.render(foo=chars) == "<*~plus>;bar<*~plus><*~plus>;bar<*~plus>"

    def test_mixed_files_ext_same_function_with_macro(self, escape_special_extensions):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(
                {
                    "macro.star": (
                        "{% macro bar() -%}bar{{ foo }}{%- endmacro %}"
                        "{% block body %}{{ foo }};{{ bar() }}{% endblock %}"
                    ),
                    "inc.foo": (
                        "{% extends 'macro.star' %}"
                        "{% block body %}"
                        "{{ super() }}{{ foo }};{{ bar () }}"
                        "{% endblock %}"
                    ),
                }
            ),
        )
        # First test simple stuff
        t = env.get_template("macro.star")
        assert t.render(foo=chars) == "<star~+>;bar<star~+>"
        t = env.get_template("inc.foo")
        assert t.render(foo=chars) == "<star~+>;bar<star~+><star~+>;bar<star~+>"

    def test_mixed_files_extends_with_macro_only_bool(self):
        chars = "<*~+>"

        loader = DictLoader(
            {
                "macro.star": (
                    "{% macro bar() -%}bar{{ foo }}{%- endmacro %}"
                    "{% block body %}{{ foo }};{{ bar() }}{% endblock %}"
                ),
                "inc.plus": (
                    "{% extends 'macro.star' %}"
                    "{% block body %}"
                    "{{ super() }}{{ foo }};{{ bar () }}"
                    "{% endblock %}"
                ),
            }
        )

        env = Environment(
            autoescape=select_autoescape(
                enabled_extensions=["star"], disabled_extensions=["plus"]
            ),
            loader=loader,
        )
        # First test simple stuff
        t = env.get_template("macro.star")
        assert t.render(foo=chars) == "&lt;*~+&gt;;bar&lt;*~+&gt;"
        t = env.get_template("inc.plus")
        # works as expected
        assert (
            t.render(foo=chars)
            == "&lt;*~+&gt;;bar&amp;lt;*~+&amp;gt;<*~+>;bar&lt;*~+&gt;"
        )

        # now invert the settings
        env = Environment(
            autoescape=select_autoescape(
                enabled_extensions=["plus"], disabled_extensions=["star"]
            ),
            loader=loader,
        )

        # First test simple stuff
        t = env.get_template("macro.star")
        assert t.render(foo=chars) == "<*~+>;bar<*~+>"
        t = env.get_template("inc.plus")
        # works as expected -> this issue is in the context with the custom escapes
        assert t.render(foo=chars) == "<*~+>;bar<*~+>&lt;*~+&gt;;bar<*~+>"

    def test_raise_exception_mixed_files_extend(self, escape_special_extensions):
        chars = "<*~+>"

        templates = {
            "main.star": "{% block body %}{{ foo }};{% endblock %}",
            "inc.star": "{% extends 'main.star' %}"
            "{% block body %}{{ super() }}{{ foo }};{% endblock %}",
            "inc.tilde": "{% extends 'main.star' %}"
            "{% block body %}{{ super() }}{{ foo }};{% endblock %}",
        }

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(templates),
        )
        # First test simple stuff
        t = env.get_template("main.star")
        assert t.render(foo=chars) == "<star~+>;"

        t = env.get_template("inc.star")
        assert t.render(foo=chars) == "<star~+>;<star~+>;"

        t = env.get_template("inc.tilde")
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)

        # Now we test als with string render, note this has the default
        # Markup escape, which is still different
        t = env.from_string(templates["inc.tilde"])
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)

    def test_raise_exception_mixed_files_include_plus_extend_with_block(
        self, escape_special_extensions
    ):
        chars = "<*~+>"

        env = Environment(
            autoescape=select_autoescape(
                special_extensions=escape_special_extensions,
                enabled_extensions=["htm", "html"],
                disabled_extensions=["txt"],
            ),
            loader=DictLoader(
                {
                    "main.star": "StarMain{{ foo }};{% include 'inc.tilde' %};",
                    "inc.plus": (
                        "PlusMain{{ foo }};"
                        "{% block body %}"
                        "PlusBody{{ foo }};"
                        "{% endblock %}"
                    ),
                    "inc.tilde": (
                        "{% extends 'inc.plus' %}"
                        "TildeMain{{ foo }};"
                        "{% block body %}"
                        "MainBody{{ foo }};"
                        "{{ super() }}"
                        "{% endblock %}"
                    ),
                }
            ),
        )
        t = env.get_template("main.star")
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)
        # Now we test als with string render, note this has the default
        # Markup escape, which is still different
        t = env.from_string("StarMain{{ foo }};{% include 'inc.tilde' %};")
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)

    def test_raise_exception_mixed_files_extends_with_macro(
        self, escape_special_extensions
    ):
        chars = "<*~+>"

        templates = {
            "macro.star": (
                "{% macro bar() -%}bar{{ foo }}{%- endmacro %}"
                "{% block body %}{{ foo }};{{ bar() }}{% endblock %}"
            ),
            "inc.plus": (
                "{% extends 'macro.star' %}"
                "{% block body %}"
                "{{ super() }}{{ foo }};{{ bar () }}"
                "{% endblock %}"
            ),
        }

        env = Environment(
            autoescape=select_autoescape(special_extensions=escape_special_extensions),
            loader=DictLoader(templates),
        )
        # First test simple stuff
        t = env.get_template("macro.star")
        assert t.render(foo=chars) == "<star~+>;bar<star~+>"
        t = env.get_template("inc.plus")
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)

        # Now we test als with string render, note this has the default
        # Markup escape, which is still different
        t = env.from_string(templates["inc.plus"])
        with pytest.raises(TemplateConfigurationError):
            # Unfortunately the error is only risen once the template
            # is rendered due to the dynamic nature of the extends
            # and includes in the template
            t.render(foo=chars)
