import pytest

from jinja2._compat import text_type
from jinja2.exceptions import UndefinedError
from jinja2.nativetypes import NativeEnvironment
from jinja2.runtime import Undefined


@pytest.fixture
def env():
    return NativeEnvironment()


class TestNativeEnvironment(object):
    def test_is_defined_native_return(self, env):
        t = env.from_string('{{ missing is defined }}')
        assert not t.render()

    def test_undefined_native_return(self, env):
        t = env.from_string('{{ missing }}')
        assert isinstance(t.render(), Undefined)

    def test_adding_undefined_native_return(self, env):
        t = env.from_string('{{ 3 + missing }}')

        with pytest.raises(UndefinedError):
            t.render()

    def test_cast_int(self, env):
        t = env.from_string("{{ anumber|int }}")
        result = t.render(anumber='3')
        assert isinstance(result, int)
        assert result == 3

    def test_list_add(self, env):
        t = env.from_string("{{ listone + listtwo }}")
        result = t.render(listone=['a', 'b'], listtwo=['c', 'd'])
        assert isinstance(result, list)
        assert result == ['a', 'b', 'c', 'd']

    def test_multi_expression_add(self, env):
        t = env.from_string("{{ listone }} + {{ listtwo }}")
        result = t.render(listone=['a', 'b'], listtwo=['c', 'd'])
        assert not isinstance(result, list)
        assert result == "['a', 'b'] + ['c', 'd']"

    def test_loops(self, env):
        t = env.from_string("{% for x in listone %}{{ x }}{% endfor %}")
        result = t.render(listone=['a', 'b', 'c', 'd'])
        assert isinstance(result, text_type)
        assert result == 'abcd'

    def test_loops_with_ints(self, env):
        t = env.from_string("{% for x in listone %}{{ x }}{% endfor %}")
        result = t.render(listone=[1, 2, 3, 4])
        assert isinstance(result, int)
        assert result == 1234

    def test_loop_look_alike(self, env):
        t = env.from_string("{% for x in listone %}{{ x }}{% endfor %}")
        result = t.render(listone=[1])
        assert isinstance(result, int)
        assert result == 1

    def test_booleans(self, env):
        t = env.from_string("{{ boolval }}")
        result = t.render(boolval=True)
        assert isinstance(result, bool)
        assert result is True

        t = env.from_string("{{ boolval }}")
        result = t.render(boolval=False)
        assert isinstance(result, bool)
        assert result is False

        t = env.from_string("{{ 1 == 1 }}")
        result = t.render()
        assert isinstance(result, bool)
        assert result is True

        t = env.from_string("{{ 2 + 2 == 5 }}")
        result = t.render()
        assert isinstance(result, bool)
        assert result is False

        t = env.from_string("{{ None == None }}")
        result = t.render()
        assert isinstance(result, bool)
        assert result is True

        t = env.from_string("{{ '' == None }}")
        result = t.render()
        assert isinstance(result, bool)
        assert result is False

    def test_variable_dunder(self, env):
        t = env.from_string("{{ x.__class__ }}")
        result = t.render(x=True)
        assert isinstance(result, type)

    def test_constant_dunder(self, env):
        t = env.from_string("{{ true.__class__ }}")
        result = t.render()
        assert isinstance(result, type)

    def test_constant_dunder_to_string(self, env):
        t = env.from_string("{{ true.__class__|string }}")
        result = t.render()
        assert not isinstance(result, type)
        assert result in ["<type 'bool'>", "<class 'bool'>"]
