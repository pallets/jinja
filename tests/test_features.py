import sys
import pytest

from jinja2 import Template, Environment, contextfilter


@pytest.mark.skipif(sys.version_info < (3, 5),
                    reason='Requires 3.5 or later')
def test_generator_stop():
    class X(object):
        def __getattr__(self, name):
            raise StopIteration()

    t = Template('a{{ bad.bar() }}b')
    with pytest.raises(RuntimeError):
        t.render(bad=X())


@pytest.mark.skipif(sys.version_info[0] > 2,
                    reason='Feature only supported on 2.x')
def test_ascii_str():
    @contextfilter
    def assert_func(context, value):
        assert type(value) is context['expected_type']

    env = Environment()
    env.filters['assert'] = assert_func

    env.policies['compiler.ascii_str'] = False
    t = env.from_string('{{ "foo"|assert }}')
    t.render(expected_type=unicode)

    env.policies['compiler.ascii_str'] = True
    t = env.from_string('{{ "foo"|assert }}')
    t.render(expected_type=str)

    for val in True, False:
        env.policies['compiler.ascii_str'] = val
        t = env.from_string(u'{{ "\N{SNOWMAN}"|assert }}')
        t.render(expected_type=unicode)
