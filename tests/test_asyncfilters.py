import pytest
from jinja2 import Environment


@pytest.fixture
def env_async():
    return Environment(enable_async=True)


def test_first(env_async):
    tmpl = env_async.from_string('{{ foo|first }}')
    out = tmpl.render(foo=list(range(10)))
    assert out == '0'


def test_first_aiter(env_async):
    async def foo():
        for x in range(10):
            yield x
    tmpl = env_async.from_string('{{ foo()|first }}')
    out = tmpl.render(foo=foo)
    assert out == '0'
