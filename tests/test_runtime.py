import copy
import itertools
import pickle

import pytest

from jinja2 import ChainableUndefined
from jinja2 import DebugUndefined
from jinja2 import StrictUndefined
from jinja2 import Template
from jinja2 import TemplateRuntimeError
from jinja2 import Undefined
from jinja2.runtime import LoopContext

TEST_IDX_TEMPLATE_STR_1 = (
    "[{% for i in lst|reverse %}(len={{ loop.length }},"
    " revindex={{ loop.revindex }}, index={{ loop.index }}, val={{ i }}){% endfor %}]"
)
TEST_IDX0_TEMPLATE_STR_1 = (
    "[{% for i in lst|reverse %}(len={{ loop.length }},"
    " revindex0={{ loop.revindex0 }}, index0={{ loop.index0 }}, val={{ i }})"
    "{% endfor %}]"
)


def test_loop_idx():
    t = Template(TEST_IDX_TEMPLATE_STR_1)
    lst = [10]
    excepted_render = "[(len=1, revindex=1, index=1, val=10)]"
    assert excepted_render == t.render(lst=lst)


def test_loop_idx0():
    t = Template(TEST_IDX0_TEMPLATE_STR_1)
    lst = [10]
    excepted_render = "[(len=1, revindex0=0, index0=0, val=10)]"
    assert excepted_render == t.render(lst=lst)


def test_loopcontext0():
    in_lst = []
    lc = LoopContext(reversed(in_lst), None)
    assert lc.length == len(in_lst)


def test_loopcontext1():
    in_lst = [10]
    lc = LoopContext(reversed(in_lst), None)
    assert lc.length == len(in_lst)


def test_loopcontext2():
    in_lst = [10, 11]
    lc = LoopContext(reversed(in_lst), None)
    assert lc.length == len(in_lst)


def test_iterator_not_advanced_early():
    t = Template("{% for _, g in gs %}{{ loop.index }} {{ g|list }}\n{% endfor %}")
    out = t.render(
        gs=itertools.groupby([(1, "a"), (1, "b"), (2, "c"), (3, "d")], lambda x: x[0])
    )
    # groupby groups depend on the current position of the iterator. If
    # it was advanced early, the lists would appear empty.
    assert out == "1 [(1, 'a'), (1, 'b')]\n2 [(2, 'c')]\n3 [(3, 'd')]\n"


def test_mock_not_pass_arg_marker():
    """If a callable class has a ``__getattr__`` that returns True-like
    values for arbitrary attrs, it should not be incorrectly identified
    as a ``pass_context`` function.
    """

    class Calc:
        def __getattr__(self, item):
            return object()

        def __call__(self, *args, **kwargs):
            return len(args) + len(kwargs)

    t = Template("{{ calc() }}")
    out = t.render(calc=Calc())
    # Would be "1" if context argument was passed.
    assert out == "0"


_undefined_types = (Undefined, ChainableUndefined, DebugUndefined, StrictUndefined)


@pytest.mark.parametrize("undefined_type", _undefined_types)
def test_undefined_copy(undefined_type):
    undef = undefined_type("a hint", ["foo"], "a name", TemplateRuntimeError)
    copied = copy.copy(undef)

    assert copied is not undef
    assert copied._undefined_hint is undef._undefined_hint
    assert copied._undefined_obj is undef._undefined_obj
    assert copied._undefined_name is undef._undefined_name
    assert copied._undefined_exception is undef._undefined_exception


@pytest.mark.parametrize("undefined_type", _undefined_types)
def test_undefined_deepcopy(undefined_type):
    undef = undefined_type("a hint", ["foo"], "a name", TemplateRuntimeError)
    copied = copy.deepcopy(undef)

    assert copied._undefined_hint is undef._undefined_hint
    assert copied._undefined_obj is not undef._undefined_obj
    assert copied._undefined_obj == undef._undefined_obj
    assert copied._undefined_name is undef._undefined_name
    assert copied._undefined_exception is undef._undefined_exception


@pytest.mark.parametrize("undefined_type", _undefined_types)
def test_undefined_pickle(undefined_type):
    undef = undefined_type("a hint", ["foo"], "a name", TemplateRuntimeError)
    copied = pickle.loads(pickle.dumps(undef))

    assert copied._undefined_hint is not undef._undefined_hint
    assert copied._undefined_hint == undef._undefined_hint
    assert copied._undefined_obj is not undef._undefined_obj
    assert copied._undefined_obj == undef._undefined_obj
    assert copied._undefined_name is not undef._undefined_name
    assert copied._undefined_name == undef._undefined_name
    assert copied._undefined_exception is undef._undefined_exception


@pytest.mark.parametrize("undefined_type", _undefined_types)
def test_undefined_cause(undefined_type):
    exception = ValueError("foo")
    try:
        raise exception
    except ValueError:
        undef = undefined_type()
    assert undef._undefined_context is exception
    try:
        undef._fail_with_undefined_error()
    except TemplateRuntimeError as exc:
        assert exc.__context__ is exception


@pytest.mark.parametrize("undefined_type", _undefined_types)
def test_undefined_no_cause(undefined_type):
    undef = undefined_type()
    assert undef._undefined_context is None
    try:
        undef._fail_with_undefined_error()
    except TemplateRuntimeError as exc:
        assert exc.__context__ is None
