import inspect
import typing as t
from functools import wraps

from .utils import _PassArg
from .utils import pass_eval_context

if t.TYPE_CHECKING:
    V = t.TypeVar("V")


def async_variant(normal_func):
    def decorator(async_func):
        pass_arg = _PassArg.from_obj(normal_func)
        need_eval_context = pass_arg is None

        if pass_arg is _PassArg.environment:

            def is_async(args):
                return args[0].is_async

        else:

            def is_async(args):
                return args[0].environment.is_async

        @wraps(normal_func)
        def wrapper(*args, **kwargs):
            b = is_async(args)

            if need_eval_context:
                args = args[1:]

            if b:
                return async_func(*args, **kwargs)

            return normal_func(*args, **kwargs)

        if need_eval_context:
            wrapper = pass_eval_context(wrapper)

        wrapper.jinja_async_variant = True
        return wrapper

    return decorator


async def auto_await(value):
    if inspect.isawaitable(value):
        return await value

    return value


async def auto_aiter(iterable):
    if hasattr(iterable, "__aiter__"):
        async for item in iterable:
            yield item
    else:
        for item in iterable:
            yield item


async def auto_to_list(
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
) -> "t.List[V]":
    seq = []

    if hasattr(value, "__aiter__"):
        async for item in t.cast(t.AsyncIterable, value):
            seq.append(item)
    else:
        for item in t.cast(t.Iterable, value):
            seq.append(item)

    return seq
