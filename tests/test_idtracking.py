from jinja2 import nodes
from jinja2.idtracking import symbols_for_node


def test_basics():
    for_loop = nodes.For(
        nodes.Name("foo", "store"),
        nodes.Name("seq", "load"),
        [nodes.Output([nodes.Name("foo", "load")])],
        [],
        None,
        False,
    )
    tmpl = nodes.Template(
        [nodes.Assign(nodes.Name("foo", "store"), nodes.Name("bar", "load")), for_loop]
    )

    sym = symbols_for_node(tmpl)
    assert sym.refs == {
        "foo": "l_0_foo",
        "bar": "l_0_bar",
        "seq": "l_0_seq",
    }
    assert sym.loads == {
        "l_0_foo": ("undefined", None),
        "l_0_bar": ("resolve", "bar"),
        "l_0_seq": ("resolve", "seq"),
    }

    sym = symbols_for_node(for_loop, sym)
    assert sym.refs == {
        "foo": "l_1_foo",
    }
    assert sym.loads == {
        "l_1_foo": ("param", None),
    }


def test_complex():
    title_block = nodes.Block(
        "title", [nodes.Output([nodes.TemplateData("Page Title")])], False, False
    )

    render_title_macro = nodes.Macro(
        "render_title",
        [nodes.Name("title", "param")],
        [],
        [
            nodes.Output(
                [
                    nodes.TemplateData('\n  <div class="title">\n    <h1>'),
                    nodes.Name("title", "load"),
                    nodes.TemplateData("</h1>\n    <p>"),
                    nodes.Name("subtitle", "load"),
                    nodes.TemplateData("</p>\n    "),
                ]
            ),
            nodes.Assign(
                nodes.Name("subtitle", "store"), nodes.Const("something else")
            ),
            nodes.Output(
                [
                    nodes.TemplateData("\n    <p>"),
                    nodes.Name("subtitle", "load"),
                    nodes.TemplateData("</p>\n  </div>\n"),
                    nodes.If(
                        nodes.Name("something", "load"),
                        [
                            nodes.Assign(
                                nodes.Name("title_upper", "store"),
                                nodes.Filter(
                                    nodes.Name("title", "load"),
                                    "upper",
                                    [],
                                    [],
                                    None,
                                    None,
                                ),
                            ),
                            nodes.Output(
                                [
                                    nodes.Name("title_upper", "load"),
                                    nodes.Call(
                                        nodes.Name("render_title", "load"),
                                        [nodes.Const("Aha")],
                                        [],
                                        None,
                                        None,
                                    ),
                                ]
                            ),
                        ],
                        [],
                        [],
                    ),
                ]
            ),
        ],
    )

    for_loop = nodes.For(
        nodes.Name("item", "store"),
        nodes.Name("seq", "load"),
        [
            nodes.Output(
                [
                    nodes.TemplateData("\n    <li>"),
                    nodes.Name("item", "load"),
                    nodes.TemplateData("</li>\n    <span>"),
                ]
            ),
            nodes.Include(nodes.Const("helper.html"), True, False),
            nodes.Output([nodes.TemplateData("</span>\n  ")]),
        ],
        [],
        None,
        False,
    )

    body_block = nodes.Block(
        "body",
        [
            nodes.Output(
                [
                    nodes.TemplateData("\n  "),
                    nodes.Call(
                        nodes.Name("render_title", "load"),
                        [nodes.Name("item", "load")],
                        [],
                        None,
                        None,
                    ),
                    nodes.TemplateData("\n  <ul>\n  "),
                ]
            ),
            for_loop,
            nodes.Output([nodes.TemplateData("\n  </ul>\n")]),
        ],
        False,
        False,
    )

    tmpl = nodes.Template(
        [
            nodes.Extends(nodes.Const("layout.html")),
            title_block,
            render_title_macro,
            body_block,
        ]
    )

    tmpl_sym = symbols_for_node(tmpl)
    assert tmpl_sym.refs == {
        "render_title": "l_0_render_title",
    }
    assert tmpl_sym.loads == {
        "l_0_render_title": ("undefined", None),
    }
    assert tmpl_sym.stores == {"render_title"}
    assert tmpl_sym.dump_stores() == {
        "render_title": "l_0_render_title",
    }

    macro_sym = symbols_for_node(render_title_macro, tmpl_sym)
    assert macro_sym.refs == {
        "subtitle": "l_1_subtitle",
        "something": "l_1_something",
        "title": "l_1_title",
        "title_upper": "l_1_title_upper",
    }
    assert macro_sym.loads == {
        "l_1_subtitle": ("resolve", "subtitle"),
        "l_1_something": ("resolve", "something"),
        "l_1_title": ("param", None),
        "l_1_title_upper": ("resolve", "title_upper"),
    }
    assert macro_sym.stores == {"title", "title_upper", "subtitle"}
    assert macro_sym.find_ref("render_title") == "l_0_render_title"
    assert macro_sym.dump_stores() == {
        "title": "l_1_title",
        "title_upper": "l_1_title_upper",
        "subtitle": "l_1_subtitle",
        "render_title": "l_0_render_title",
    }

    body_sym = symbols_for_node(body_block)
    assert body_sym.refs == {
        "item": "l_0_item",
        "seq": "l_0_seq",
        "render_title": "l_0_render_title",
    }
    assert body_sym.loads == {
        "l_0_item": ("resolve", "item"),
        "l_0_seq": ("resolve", "seq"),
        "l_0_render_title": ("resolve", "render_title"),
    }
    assert body_sym.stores == set()

    for_sym = symbols_for_node(for_loop, body_sym)
    assert for_sym.refs == {
        "item": "l_1_item",
    }
    assert for_sym.loads == {
        "l_1_item": ("param", None),
    }
    assert for_sym.stores == {"item"}
    assert for_sym.dump_stores() == {
        "item": "l_1_item",
    }


def test_if_branching_stores():
    tmpl = nodes.Template(
        [
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("variable", "store"), nodes.Const(42))],
                [],
                [],
            )
        ]
    )

    sym = symbols_for_node(tmpl)
    assert sym.refs == {"variable": "l_0_variable", "expression": "l_0_expression"}
    assert sym.stores == {"variable"}
    assert sym.loads == {
        "l_0_variable": ("resolve", "variable"),
        "l_0_expression": ("resolve", "expression"),
    }
    assert sym.dump_stores() == {
        "variable": "l_0_variable",
    }


def test_if_branching_stores_undefined():
    tmpl = nodes.Template(
        [
            nodes.Assign(nodes.Name("variable", "store"), nodes.Const(23)),
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("variable", "store"), nodes.Const(42))],
                [],
                [],
            ),
        ]
    )

    sym = symbols_for_node(tmpl)
    assert sym.refs == {"variable": "l_0_variable", "expression": "l_0_expression"}
    assert sym.stores == {"variable"}
    assert sym.loads == {
        "l_0_variable": ("undefined", None),
        "l_0_expression": ("resolve", "expression"),
    }
    assert sym.dump_stores() == {
        "variable": "l_0_variable",
    }


def test_if_branching_multi_scope():
    for_loop = nodes.For(
        nodes.Name("item", "store"),
        nodes.Name("seq", "load"),
        [
            nodes.If(
                nodes.Name("expression", "load"),
                [nodes.Assign(nodes.Name("x", "store"), nodes.Const(42))],
                [],
                [],
            ),
            nodes.Include(nodes.Const("helper.html"), True, False),
        ],
        [],
        None,
        False,
    )

    tmpl = nodes.Template(
        [nodes.Assign(nodes.Name("x", "store"), nodes.Const(23)), for_loop]
    )

    tmpl_sym = symbols_for_node(tmpl)
    for_sym = symbols_for_node(for_loop, tmpl_sym)
    assert for_sym.stores == {"item", "x"}
    assert for_sym.loads == {
        "l_1_x": ("alias", "l_0_x"),
        "l_1_item": ("param", None),
        "l_1_expression": ("resolve", "expression"),
    }
