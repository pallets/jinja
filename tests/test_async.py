import pytest
import asyncio

from jinja2 import Template
from jinja2.utils import have_async_gen


def run(func):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(func())


@pytest.mark.skipif(not have_async_gen, reason='No async generators')
def test_basic_async():
    t = Template('{% for item in [1, 2, 3] %}[{{ item }}]{% endfor %}',
                 enable_async=True)
    async def func():
        return await t.render_async()

    rv = run(func)
    assert rv == '[1][2][3]'
