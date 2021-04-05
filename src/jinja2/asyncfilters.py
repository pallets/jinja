import typing
import typing as t
from functools import wraps
from itertools import groupby

from . import filters
from .asyncsupport import auto_aiter
from .asyncsupport import auto_await

if t.TYPE_CHECKING:
    from .environment import Environment
    from .nodes import EvalContext
    from .runtime import Context
    from .runtime import Undefined

    V = t.TypeVar("V")


async def auto_to_seq(
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


async def async_select_or_reject(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    args: t.Tuple,
    kwargs: t.Dict[str, t.Any],
    modfunc: t.Callable[[t.Any], t.Any],
    lookup_attr: bool,
) -> "t.AsyncIterator[V]":
    if value:
        func = filters.prepare_select_or_reject(
            context, args, kwargs, modfunc, lookup_attr
        )

        async for item in auto_aiter(value):
            if func(item):
                yield item


def dualfilter(normal_filter, async_filter):
    wrap_evalctx = False

    if getattr(normal_filter, "environmentfilter", False) is True:

        def is_async(args):
            return args[0].is_async

        wrap_evalctx = False
    else:
        has_evalctxfilter = getattr(normal_filter, "evalcontextfilter", False) is True
        has_ctxfilter = getattr(normal_filter, "contextfilter", False) is True
        wrap_evalctx = not has_evalctxfilter and not has_ctxfilter

        def is_async(args):
            return args[0].environment.is_async

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

    wrapper.asyncfiltervariant = True
    return wrapper


def asyncfiltervariant(original):
    def decorator(f):
        return dualfilter(original, f)

    return decorator


@asyncfiltervariant(filters.do_first)
async def do_first(
    environment: "Environment", seq: "t.Union[t.AsyncIterable[V], t.Iterable[V]]"
) -> "t.Union[V, Undefined]":
    try:
        return t.cast("V", await auto_aiter(seq).__anext__())
    except StopAsyncIteration:
        return environment.undefined("No first item, sequence was empty.")


@asyncfiltervariant(filters.do_groupby)
async def do_groupby(
    environment: "Environment",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    attribute: t.Union[str, int],
) -> "t.List[t.Tuple[t.Any, t.List[V]]]":
    expr = filters.make_attrgetter(environment, attribute)
    return [
        filters._GroupTuple(key, await auto_to_seq(values))
        for key, values in groupby(sorted(await auto_to_seq(value), key=expr), expr)
    ]


@asyncfiltervariant(filters.do_join)
async def do_join(
    eval_ctx: "EvalContext",
    value: t.Union[t.AsyncIterable, t.Iterable],
    d: str = "",
    attribute: t.Optional[t.Union[str, int]] = None,
) -> str:
    return filters.do_join(eval_ctx, await auto_to_seq(value), d, attribute)


@asyncfiltervariant(filters.do_list)
async def do_list(value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]") -> "t.List[V]":
    return await auto_to_seq(value)


@asyncfiltervariant(filters.do_reject)
async def do_reject(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: not x, False)


@asyncfiltervariant(filters.do_rejectattr)
async def do_rejectattr(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: not x, True)


@asyncfiltervariant(filters.do_select)
async def do_select(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: x, False)


@asyncfiltervariant(filters.do_selectattr)
async def do_selectattr(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: x, True)


@typing.overload
def do_map(
    context: "Context",
    value: t.Union[t.AsyncIterable, t.Iterable],
    name: str,
    *args: t.Any,
    **kwargs: t.Any,
) -> t.Iterable:
    ...


@typing.overload
def do_map(
    context: "Context",
    value: t.Union[t.AsyncIterable, t.Iterable],
    *,
    attribute: str = ...,
    default: t.Optional[t.Any] = None,
) -> t.Iterable:
    ...


@asyncfiltervariant(filters.do_map)
async def do_map(context, value, *args, **kwargs):
    if value:
        func = filters.prepare_map(context, args, kwargs)

        async for item in auto_aiter(value):
            yield await auto_await(func(item))


@asyncfiltervariant(filters.do_sum)
async def do_sum(
    environment: "Environment",
    iterable: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    attribute: t.Optional[t.Union[str, int]] = None,
    start: "V" = 0,  # type: ignore
) -> "V":
    rv = start

    if attribute is not None:
        func = filters.make_attrgetter(environment, attribute)
    else:

        def func(x):
            return x

    async for item in auto_aiter(iterable):
        rv += func(item)

    return rv


@asyncfiltervariant(filters.do_slice)
async def do_slice(
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    slices: int,
    fill_with: t.Optional[t.Any] = None,
) -> "t.Iterator[t.List[V]]":
    return filters.do_slice(await auto_to_seq(value), slices, fill_with)


ASYNC_FILTERS = {
    "first": do_first,
    "groupby": do_groupby,
    "join": do_join,
    "list": do_list,
    # we intentionally do not support do_last because it may not be safe in async
    "reject": do_reject,
    "rejectattr": do_rejectattr,
    "map": do_map,
    "select": do_select,
    "selectattr": do_selectattr,
    "sum": do_sum,
    "slice": do_slice,
}
