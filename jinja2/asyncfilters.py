from functools import wraps
from jinja2.asyncsupport import auto_aiter
from jinja2 import filters


async def auto_to_seq(value):
    seq = []
    if hasattr(value, '__aiter__'):
        async for item in value:
            seq.append(item)
    else:
        for item in value:
            seq.append(item)
    return seq


def dualfilter(normal_filter, async_filter):
    wrap_evalctx = False
    if getattr(normal_filter, 'environmentfilter'):
        is_async = lambda args: args[0].is_async
        wrap_evalctx = False
    else:
        if not getattr(normal_filter, 'evalcontextfilter'):
            wrap_evalctx = True
        is_async = lambda args: args[0].environment.is_async

    @wraps(normal_filter)
    def wrapper(*args, **kwargs):
        b = is_async(args)
        if wrap_evalctx:
            args = args[1:]
        if b:
            return async_filter(*args, **kwargs)
        return normal_filter(*args, **kwargs)

    if wrap_evalctx:
        wrapper.evalcontextfilter = True

    return wrapper


def asyncfiltervariant(original):
    def decorator(f):
        return dualfilter(original, f)
    return decorator


@asyncfiltervariant(filters.do_first)
async def do_first(environment, seq):
    try:
        return await auto_aiter(seq).__anext__()
    except StopAsyncIteration:
        return environment.undefined('No first item, sequence was empty.')


ASYNC_FILTERS = {
    'first':        do_first,
}
