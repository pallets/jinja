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


async def async_do_first(environment, seq):
    try:
        return await auto_aiter(seq).__anext__()
    except StopAsyncIteration:
        return environment.undefined('No first item, sequence was empty.')


@wraps(filters.do_first)
@filters.environmentfilter
def do_first(environment, seq):
    if environment.is_async:
        return async_do_first(environment, seq)
    return filters.do_first(environment, seq)


ASYNC_FILTERS = {
    'first': do_first,
}
