import pytest

from jinja2 import Template


# Python < 3.7
def test_generator_stop():
    class X:
        def __getattr__(self, name):
            raise StopIteration()

    t = Template("a{{ bad.bar() }}b")
    with pytest.raises(RuntimeError):
        t.render(bad=X())
