# -*- coding: utf-8 -*-
import re

import pytest

from jinja2 import contextfunction
from jinja2 import DictLoader
from jinja2 import Environment
from jinja2 import nodes
from jinja2._compat import BytesIO
from jinja2._compat import itervalues
from jinja2._compat import text_type
from jinja2.exceptions import TemplateAssertionError
from jinja2.ext import Extension
from jinja2.lexer import count_newlines
from jinja2.lexer import Token

importable_object = 23

_gettext_re = re.compile(r"_\((.*?)\)", re.DOTALL)


i18n_templates = {
    "master.html": '<title>{{ page_title|default(_("missing")) }}</title>'
    "{% block body %}{% endblock %}",
    "child.html": '{% extends "master.html" %}{% block body %}'
    "{% trans %}watch out{% endtrans %}{% endblock %}",
    "plural.html": "{% trans user_count %}One user online{% pluralize %}"
    "{{ user_count }} users online{% endtrans %}",
    "plural2.html": "{% trans user_count=get_user_count() %}{{ user_count }}s"
    "{% pluralize %}{{ user_count }}p{% endtrans %}",
    "stringformat.html": '{{ _("User: %(num)s")|format(num=user_count) }}',
}

newstyle_i18n_templates = {
    "master.html": '<title>{{ page_title|default(_("missing")) }}</title>'
    "{% block body %}{% endblock %}",
    "child.html": '{% extends "master.html" %}{% block body %}'
    "{% trans %}watch out{% endtrans %}{% endblock %}",
    "plural.html": "{% trans user_count %}One user online{% pluralize %}"
    "{{ user_count }} users online{% endtrans %}",
    "stringformat.html": '{{ _("User: %(num)s", num=user_count) }}',
    "ngettext.html": '{{ ngettext("%(num)s apple", "%(num)s apples", apples) }}',
    "ngettext_long.html": "{% trans num=apples %}{{ num }} apple{% pluralize %}"
    "{{ num }} apples{% endtrans %}",
    "transvars1.html": "{% trans %}User: {{ num }}{% endtrans %}",
    "transvars2.html": "{% trans num=count %}User: {{ num }}{% endtrans %}",
    "transvars3.html": "{% trans count=num %}User: {{ count }}{% endtrans %}",
    "novars.html": "{% trans %}%(hello)s{% endtrans %}",
    "vars.html": "{% trans %}{{ foo }}%(foo)s{% endtrans %}",
    "explicitvars.html": '{% trans foo="42" %}%(foo)s{% endtrans %}',
}


languages = {
    "de": {
        "missing": u"fehlend",
        "watch out": u"pass auf",
        "One user online": u"Ein Benutzer online",
        "%(user_count)s users online": u"%(user_count)s Benutzer online",
        "User: %(num)s": u"Benutzer: %(num)s",
        "User: %(count)s": u"Benutzer: %(count)s",
        "%(num)s apple": u"%(num)s Apfel",
        "%(num)s apples": u"%(num)s Äpfel",
    }
}


@contextfunction
def gettext(context, string):
    language = context.get("LANGUAGE", "en")
    return languages.get(language, {}).get(string, string)


@contextfunction
def ngettext(context, s, p, n):
    language = context.get("LANGUAGE", "en")
    if n != 1:
        return languages.get(language, {}).get(p, p)
    return languages.get(language, {}).get(s, s)


i18n_env = Environment(
    loader=DictLoader(i18n_templates), extensions=["jinja2.ext.i18n"]
)
i18n_env.globals.update({"_": gettext, "gettext": gettext, "ngettext": ngettext})
i18n_env_trimmed = Environment(extensions=["jinja2.ext.i18n"])
i18n_env_trimmed.policies["ext.i18n.trimmed"] = True
i18n_env_trimmed.globals.update(
    {"_": gettext, "gettext": gettext, "ngettext": ngettext}
)

newstyle_i18n_env = Environment(
    loader=DictLoader(newstyle_i18n_templates), extensions=["jinja2.ext.i18n"]
)
newstyle_i18n_env.install_gettext_callables(gettext, ngettext, newstyle=True)


class ExampleExtension(Extension):
    tags = set(["test"])
    ext_attr = 42
    context_reference_node_cls = nodes.ContextReference

    def parse(self, parser):
        return nodes.Output(
            [
                self.call_method(
                    "_dump",
                    [
                        nodes.EnvironmentAttribute("sandboxed"),
                        self.attr("ext_attr"),
                        nodes.ImportedName(__name__ + ".importable_object"),
                        self.context_reference_node_cls(),
                    ],
                )
            ]
        ).set_lineno(next(parser.stream).lineno)

    def _dump(self, sandboxed, ext_attr, imported_object, context):
        return "%s|%s|%s|%s|%s" % (
            sandboxed,
            ext_attr,
            imported_object,
            context.blocks,
            context.get("test_var"),
        )


class DerivedExampleExtension(ExampleExtension):
    context_reference_node_cls = nodes.DerivedContextReference


class PreprocessorExtension(Extension):
    def preprocess(self, source, name, filename=None):
        return source.replace("[[TEST]]", "({{ foo }})")


class StreamFilterExtension(Extension):
    def filter_stream(self, stream):
        for token in stream:
            if token.type == "data":
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
            value = token.value[pos : match.start()]
            if value:
                yield Token(lineno, "data", value)
            lineno += count_newlines(token.value)
            yield Token(lineno, "variable_begin", None)
            yield Token(lineno, "name", "gettext")
            yield Token(lineno, "lparen", None)
            yield Token(lineno, "string", match.group(1))
            yield Token(lineno, "rparen", None)
            yield Token(lineno, "variable_end", None)
            pos = match.end()
        if pos < end:
            yield Token(lineno, "data", token.value[pos:])


class TestExtensions(object):
    def test_extend_late(self):
        env = Environment()
        env.add_extension("jinja2.ext.autoescape")
        t = env.from_string('{% autoescape true %}{{ "<test>" }}{% endautoescape %}')
        assert t.render() == "&lt;test&gt;"

    def test_loop_controls(self):
        env = Environment(extensions=["jinja2.ext.loopcontrols"])

        tmpl = env.from_string(
            """
            {%- for item in [1, 2, 3, 4] %}
                {%- if item % 2 == 0 %}{% continue %}{% endif -%}
                {{ item }}
            {%- endfor %}"""
        )
        assert tmpl.render() == "13"

        tmpl = env.from_string(
            """
            {%- for item in [1, 2, 3, 4] %}
                {%- if item > 2 %}{% break %}{% endif -%}
                {{ item }}
            {%- endfor %}"""
        )
        assert tmpl.render() == "12"

    def test_do(self):
        env = Environment(extensions=["jinja2.ext.do"])
        tmpl = env.from_string(
            """
            {%- set items = [] %}
            {%- for char in "foo" %}
                {%- do items.append(loop.index0 ~ char) %}
            {%- endfor %}{{ items|join(', ') }}"""
        )
        assert tmpl.render() == "0f, 1o, 2o"

    def test_extension_nodes(self):
        env = Environment(extensions=[ExampleExtension])
        tmpl = env.from_string("{% test %}")
        assert tmpl.render() == "False|42|23|{}|None"

    def test_contextreference_node_passes_context(self):
        env = Environment(extensions=[ExampleExtension])
        tmpl = env.from_string('{% set test_var="test_content" %}{% test %}')
        assert tmpl.render() == "False|42|23|{}|test_content"

    def test_contextreference_node_can_pass_locals(self):
        env = Environment(extensions=[DerivedExampleExtension])
        tmpl = env.from_string(
            '{% for test_var in ["test_content"] %}{% test %}{% endfor %}'
        )
        assert tmpl.render() == "False|42|23|{}|test_content"

    def test_identifier(self):
        assert ExampleExtension.identifier == __name__ + ".ExampleExtension"

    def test_rebinding(self):
        original = Environment(extensions=[ExampleExtension])
        overlay = original.overlay()
        for env in original, overlay:
            for ext in itervalues(env.extensions):
                assert ext.environment is env

    def test_preprocessor_extension(self):
        env = Environment(extensions=[PreprocessorExtension])
        tmpl = env.from_string("{[[TEST]]}")
        assert tmpl.render(foo=42) == "{(42)}"

    def test_streamfilter_extension(self):
        env = Environment(extensions=[StreamFilterExtension])
        env.globals["gettext"] = lambda x: x.upper()
        tmpl = env.from_string("Foo _(bar) Baz")
        out = tmpl.render()
        assert out == "Foo BAR Baz"

    def test_extension_ordering(self):
        class T1(Extension):
            priority = 1

        class T2(Extension):
            priority = 2

        env = Environment(extensions=[T1, T2])
        ext = list(env.iter_extensions())
        assert ext[0].__class__ is T1
        assert ext[1].__class__ is T2

    def test_debug(self):
        env = Environment(extensions=["jinja2.ext.debug"])
        t = env.from_string("Hello\n{% debug %}\nGoodbye")
        out = t.render()

        for value in ("context", "cycler", "filters", "abs", "tests", "!="):
            assert "'{}'".format(value) in out


class TestInternationalization(object):
    def test_trans(self):
        tmpl = i18n_env.get_template("child.html")
        assert tmpl.render(LANGUAGE="de") == "<title>fehlend</title>pass auf"

    def test_trans_plural(self):
        tmpl = i18n_env.get_template("plural.html")
        assert tmpl.render(LANGUAGE="de", user_count=1) == "Ein Benutzer online"
        assert tmpl.render(LANGUAGE="de", user_count=2) == "2 Benutzer online"

    def test_trans_plural_with_functions(self):
        tmpl = i18n_env.get_template("plural2.html")

        def get_user_count():
            get_user_count.called += 1
            return 1

        get_user_count.called = 0
        assert tmpl.render(LANGUAGE="de", get_user_count=get_user_count) == "1s"
        assert get_user_count.called == 1

    def test_complex_plural(self):
        tmpl = i18n_env.from_string(
            "{% trans foo=42, count=2 %}{{ count }} item{% "
            "pluralize count %}{{ count }} items{% endtrans %}"
        )
        assert tmpl.render() == "2 items"
        pytest.raises(
            TemplateAssertionError,
            i18n_env.from_string,
            "{% trans foo %}...{% pluralize bar %}...{% endtrans %}",
        )

    def test_trans_stringformatting(self):
        tmpl = i18n_env.get_template("stringformat.html")
        assert tmpl.render(LANGUAGE="de", user_count=5) == "Benutzer: 5"

    def test_trimmed(self):
        tmpl = i18n_env.from_string(
            "{%- trans trimmed %}  hello\n  world  {% endtrans -%}"
        )
        assert tmpl.render() == "hello world"

    def test_trimmed_policy(self):
        s = "{%- trans %}  hello\n  world  {% endtrans -%}"
        tmpl = i18n_env.from_string(s)
        trimmed_tmpl = i18n_env_trimmed.from_string(s)
        assert tmpl.render() == "  hello\n  world  "
        assert trimmed_tmpl.render() == "hello world"

    def test_trimmed_policy_override(self):
        tmpl = i18n_env_trimmed.from_string(
            "{%- trans notrimmed %}  hello\n  world  {% endtrans -%}"
        )
        assert tmpl.render() == "  hello\n  world  "

    def test_trimmed_vars(self):
        tmpl = i18n_env.from_string(
            '{%- trans trimmed x="world" %}  hello\n  {{ x }} {% endtrans -%}'
        )
        assert tmpl.render() == "hello world"

    def test_trimmed_varname_trimmed(self):
        # unlikely variable name, but when used as a variable
        # it should not enable trimming
        tmpl = i18n_env.from_string(
            "{%- trans trimmed = 'world' %}  hello\n  {{ trimmed }}  {% endtrans -%}"
        )
        assert tmpl.render() == "  hello\n  world  "

    def test_extract(self):
        from jinja2.ext import babel_extract

        source = BytesIO(
            """
        {{ gettext('Hello World') }}
        {% trans %}Hello World{% endtrans %}
        {% trans %}{{ users }} user{% pluralize %}{{ users }} users{% endtrans %}
        """.encode(
                "ascii"
            )
        )  # make python 3 happy
        assert list(babel_extract(source, ("gettext", "ngettext", "_"), [], {})) == [
            (2, "gettext", u"Hello World", []),
            (3, "gettext", u"Hello World", []),
            (4, "ngettext", (u"%(users)s user", u"%(users)s users", None), []),
        ]

    def test_extract_trimmed(self):
        from jinja2.ext import babel_extract

        source = BytesIO(
            """
        {{ gettext(' Hello  \n  World') }}
        {% trans trimmed %} Hello  \n  World{% endtrans %}
        {% trans trimmed %}{{ users }} \n user
        {%- pluralize %}{{ users }} \n users{% endtrans %}
        """.encode(
                "ascii"
            )
        )  # make python 3 happy
        assert list(babel_extract(source, ("gettext", "ngettext", "_"), [], {})) == [
            (2, "gettext", u" Hello  \n  World", []),
            (4, "gettext", u"Hello World", []),
            (6, "ngettext", (u"%(users)s user", u"%(users)s users", None), []),
        ]

    def test_extract_trimmed_option(self):
        from jinja2.ext import babel_extract

        source = BytesIO(
            """
        {{ gettext(' Hello  \n  World') }}
        {% trans %} Hello  \n  World{% endtrans %}
        {% trans %}{{ users }} \n user
        {%- pluralize %}{{ users }} \n users{% endtrans %}
        """.encode(
                "ascii"
            )
        )  # make python 3 happy
        opts = {"trimmed": "true"}
        assert list(babel_extract(source, ("gettext", "ngettext", "_"), [], opts)) == [
            (2, "gettext", u" Hello  \n  World", []),
            (4, "gettext", u"Hello World", []),
            (6, "ngettext", (u"%(users)s user", u"%(users)s users", None), []),
        ]

    def test_comment_extract(self):
        from jinja2.ext import babel_extract

        source = BytesIO(
            """
        {# trans first #}
        {{ gettext('Hello World') }}
        {% trans %}Hello World{% endtrans %}{# trans second #}
        {#: third #}
        {% trans %}{{ users }} user{% pluralize %}{{ users }} users{% endtrans %}
        """.encode(
                "utf-8"
            )
        )  # make python 3 happy
        assert list(
            babel_extract(source, ("gettext", "ngettext", "_"), ["trans", ":"], {})
        ) == [
            (3, "gettext", u"Hello World", ["first"]),
            (4, "gettext", u"Hello World", ["second"]),
            (6, "ngettext", (u"%(users)s user", u"%(users)s users", None), ["third"]),
        ]


class TestScope(object):
    def test_basic_scope_behavior(self):
        # This is what the old with statement compiled down to
        class ScopeExt(Extension):
            tags = set(["scope"])

            def parse(self, parser):
                node = nodes.Scope(lineno=next(parser.stream).lineno)
                assignments = []
                while parser.stream.current.type != "block_end":
                    lineno = parser.stream.current.lineno
                    if assignments:
                        parser.stream.expect("comma")
                    target = parser.parse_assign_target()
                    parser.stream.expect("assign")
                    expr = parser.parse_expression()
                    assignments.append(nodes.Assign(target, expr, lineno=lineno))
                node.body = assignments + list(
                    parser.parse_statements(("name:endscope",), drop_needle=True)
                )
                return node

        env = Environment(extensions=[ScopeExt])
        tmpl = env.from_string(
            """\
        {%- scope a=1, b=2, c=b, d=e, e=5 -%}
            {{ a }}|{{ b }}|{{ c }}|{{ d }}|{{ e }}
        {%- endscope -%}
        """
        )
        assert tmpl.render(b=3, e=4) == "1|2|2|4|5"


class TestNewstyleInternationalization(object):
    def test_trans(self):
        tmpl = newstyle_i18n_env.get_template("child.html")
        assert tmpl.render(LANGUAGE="de") == "<title>fehlend</title>pass auf"

    def test_trans_plural(self):
        tmpl = newstyle_i18n_env.get_template("plural.html")
        assert tmpl.render(LANGUAGE="de", user_count=1) == "Ein Benutzer online"
        assert tmpl.render(LANGUAGE="de", user_count=2) == "2 Benutzer online"

    def test_complex_plural(self):
        tmpl = newstyle_i18n_env.from_string(
            "{% trans foo=42, count=2 %}{{ count }} item{% "
            "pluralize count %}{{ count }} items{% endtrans %}"
        )
        assert tmpl.render() == "2 items"
        pytest.raises(
            TemplateAssertionError,
            i18n_env.from_string,
            "{% trans foo %}...{% pluralize bar %}...{% endtrans %}",
        )

    def test_trans_stringformatting(self):
        tmpl = newstyle_i18n_env.get_template("stringformat.html")
        assert tmpl.render(LANGUAGE="de", user_count=5) == "Benutzer: 5"

    def test_newstyle_plural(self):
        tmpl = newstyle_i18n_env.get_template("ngettext.html")
        assert tmpl.render(LANGUAGE="de", apples=1) == "1 Apfel"
        assert tmpl.render(LANGUAGE="de", apples=5) == u"5 Äpfel"

    def test_autoescape_support(self):
        env = Environment(extensions=["jinja2.ext.autoescape", "jinja2.ext.i18n"])
        env.install_gettext_callables(
            lambda x: u"<strong>Wert: %(name)s</strong>",
            lambda s, p, n: s,
            newstyle=True,
        )
        t = env.from_string(
            '{% autoescape ae %}{{ gettext("foo", name='
            '"<test>") }}{% endautoescape %}'
        )
        assert t.render(ae=True) == "<strong>Wert: &lt;test&gt;</strong>"
        assert t.render(ae=False) == "<strong>Wert: <test></strong>"

    def test_autoescape_macros(self):
        env = Environment(autoescape=False, extensions=["jinja2.ext.autoescape"])
        template = (
            "{% macro m() %}<html>{% endmacro %}"
            "{% autoescape true %}{{ m() }}{% endautoescape %}"
        )
        assert env.from_string(template).render() == "<html>"

    def test_num_used_twice(self):
        tmpl = newstyle_i18n_env.get_template("ngettext_long.html")
        assert tmpl.render(apples=5, LANGUAGE="de") == u"5 Äpfel"

    def test_num_called_num(self):
        source = newstyle_i18n_env.compile(
            """
            {% trans num=3 %}{{ num }} apple{% pluralize
            %}{{ num }} apples{% endtrans %}
        """,
            raw=True,
        )
        # quite hacky, but the only way to properly test that.  The idea is
        # that the generated code does not pass num twice (although that
        # would work) for better performance.  This only works on the
        # newstyle gettext of course
        assert (
            re.search(r"u?'\%\(num\)s apple', u?'\%\(num\)s " r"apples', 3", source)
            is not None
        )

    def test_trans_vars(self):
        t1 = newstyle_i18n_env.get_template("transvars1.html")
        t2 = newstyle_i18n_env.get_template("transvars2.html")
        t3 = newstyle_i18n_env.get_template("transvars3.html")
        assert t1.render(num=1, LANGUAGE="de") == "Benutzer: 1"
        assert t2.render(count=23, LANGUAGE="de") == "Benutzer: 23"
        assert t3.render(num=42, LANGUAGE="de") == "Benutzer: 42"

    def test_novars_vars_escaping(self):
        t = newstyle_i18n_env.get_template("novars.html")
        assert t.render() == "%(hello)s"
        t = newstyle_i18n_env.get_template("vars.html")
        assert t.render(foo="42") == "42%(foo)s"
        t = newstyle_i18n_env.get_template("explicitvars.html")
        assert t.render() == "%(foo)s"


class TestAutoEscape(object):
    def test_scoped_setting(self):
        env = Environment(extensions=["jinja2.ext.autoescape"], autoescape=True)
        tmpl = env.from_string(
            """
            {{ "<HelloWorld>" }}
            {% autoescape false %}
                {{ "<HelloWorld>" }}
            {% endautoescape %}
            {{ "<HelloWorld>" }}
        """
        )
        assert tmpl.render().split() == [
            u"&lt;HelloWorld&gt;",
            u"<HelloWorld>",
            u"&lt;HelloWorld&gt;",
        ]

        env = Environment(extensions=["jinja2.ext.autoescape"], autoescape=False)
        tmpl = env.from_string(
            """
            {{ "<HelloWorld>" }}
            {% autoescape true %}
                {{ "<HelloWorld>" }}
            {% endautoescape %}
            {{ "<HelloWorld>" }}
        """
        )
        assert tmpl.render().split() == [
            u"<HelloWorld>",
            u"&lt;HelloWorld&gt;",
            u"<HelloWorld>",
        ]

    def test_nonvolatile(self):
        env = Environment(extensions=["jinja2.ext.autoescape"], autoescape=True)
        tmpl = env.from_string('{{ {"foo": "<test>"}|xmlattr|escape }}')
        assert tmpl.render() == ' foo="&lt;test&gt;"'
        tmpl = env.from_string(
            '{% autoescape false %}{{ {"foo": "<test>"}'
            "|xmlattr|escape }}{% endautoescape %}"
        )
        assert tmpl.render() == " foo=&#34;&amp;lt;test&amp;gt;&#34;"

    def test_volatile(self):
        env = Environment(extensions=["jinja2.ext.autoescape"], autoescape=True)
        tmpl = env.from_string(
            '{% autoescape foo %}{{ {"foo": "<test>"}'
            "|xmlattr|escape }}{% endautoescape %}"
        )
        assert tmpl.render(foo=False) == " foo=&#34;&amp;lt;test&amp;gt;&#34;"
        assert tmpl.render(foo=True) == ' foo="&lt;test&gt;"'

    def test_scoping(self):
        env = Environment(extensions=["jinja2.ext.autoescape"])
        tmpl = env.from_string(
            '{% autoescape true %}{% set x = "<x>" %}{{ x }}'
            '{% endautoescape %}{{ x }}{{ "<y>" }}'
        )
        assert tmpl.render(x=1) == "&lt;x&gt;1<y>"

    def test_volatile_scoping(self):
        env = Environment(extensions=["jinja2.ext.autoescape"])
        tmplsource = """
        {% autoescape val %}
            {% macro foo(x) %}
                [{{ x }}]
            {% endmacro %}
            {{ foo().__class__.__name__ }}
        {% endautoescape %}
        {{ '<testing>' }}
        """
        tmpl = env.from_string(tmplsource)
        assert tmpl.render(val=True).split()[0] == "Markup"
        assert tmpl.render(val=False).split()[0] == text_type.__name__

        # looking at the source we should see <testing> there in raw
        # (and then escaped as well)
        env = Environment(extensions=["jinja2.ext.autoescape"])
        pysource = env.compile(tmplsource, raw=True)
        assert "<testing>\\n" in pysource

        env = Environment(extensions=["jinja2.ext.autoescape"], autoescape=True)
        pysource = env.compile(tmplsource, raw=True)
        assert "&lt;testing&gt;\\n" in pysource

    def test_overlay_scopes(self):
        class MagicScopeExtension(Extension):
            tags = set(["overlay"])

            def parse(self, parser):
                node = nodes.OverlayScope(lineno=next(parser.stream).lineno)
                node.body = list(
                    parser.parse_statements(("name:endoverlay",), drop_needle=True)
                )
                node.context = self.call_method("get_scope")
                return node

            def get_scope(self):
                return {"x": [1, 2, 3]}

        env = Environment(extensions=[MagicScopeExtension])

        tmpl = env.from_string(
            """
            {{- x }}|{% set z = 99 %}
            {%- overlay %}
                {{- y }}|{{ z }}|{% for item in x %}[{{ item }}]{% endfor %}
            {%- endoverlay %}|
            {{- x -}}
        """
        )
        assert tmpl.render(x=42, y=23) == "42|23|99|[1][2][3]|42"
