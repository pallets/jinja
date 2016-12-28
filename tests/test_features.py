import sys
import pytest

from jinja2 import Template


@pytest.mark.skipif(sys.version_info < (3, 5),
                    reason='Requires 3.5 or later')
def test_generator_stop():
    class X(object):
        def __getattr__(self, name):
            raise StopIteration()

    t = Template('a{{ bad.bar() }}b')
    with pytest.raises(RuntimeError):
        t.render(bad=X())
