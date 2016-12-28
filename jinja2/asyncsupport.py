import sys
import asyncio
import inspect

from jinja2.utils import concat


async def render_async(self, *args, **kwargs):
    if not self.environment._async:
        raise RuntimeError('The environment was not created with async mode '
                           'enabled.')

    vars = dict(*args, **kwargs)
    ctx = self.new_context(vars)
    rv = []
    async def collect():
        async for event in self.root_render_func(ctx):
            rv.append(event)

    try:
        await collect()
        return concat(rv)
    except Exception:
        exc_info = sys.exc_info()
    return self.environment.handle_exception(exc_info, True)


def wrap_render_func(original_render):
    def render(self, *args, **kwargs):
        if not self.environment._async:
            return original_render(self, *args, **kwargs)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.render_async(self, *args, **kwargs))
    return render


def patch_template():
    from jinja2 import Template
    Template.render_async = render_async
    Template.render = wrap_render_func(Template.render)


def patch_all():
    patch_template()


async def auto_await(value):
    if inspect.isawaitable(value):
        return await value
    return value
