import typing
import typing as t
import warnings
from functools import wraps
from itertools import groupby

from . import filters
from .asyncsupport import auto_aiter
from .asyncsupport import auto_await
from .utils import _PassArg
from .utils import pass_eval_context

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


def dual_filter(normal_func, async_func):
    pass_arg = _PassArg.from_obj(normal_func)
    wrapper_has_eval_context = False

    if pass_arg is _PassArg.environment:
        wrapper_has_eval_context = False

        def is_async(args):
            return args[0].is_async

    else:
        wrapper_has_eval_context = pass_arg is None

        def is_async(args):
            return args[0].environment.is_async

    @wraps(normal_func)
    def wrapper(*args, **kwargs):
        b = is_async(args)

        if wrapper_has_eval_context:
            args = args[1:]

        if b:
            return async_func(*args, **kwargs)

        return normal_func(*args, **kwargs)

    if wrapper_has_eval_context:
        wrapper = pass_eval_context(wrapper)

    wrapper.jinja_async_variant = True
    return wrapper


def async_variant(original):
    def decorator(f):
        return dual_filter(original, f)

    return decorator


def asyncfiltervariant(original):
    warnings.warn(
        "'asyncfiltervariant' is renamed to 'async_variant', the old"
        " name will be removed in Jinja 3.1.",
        DeprecationWarning,
        stacklevel=2,
    )
    return async_variant(original)


@async_variant(filters.do_first)
async def do_first(
    environment: "Environment", seq: "t.Union[t.AsyncIterable[V], t.Iterable[V]]"
) -> "t.Union[V, Undefined]":
    try:
        return t.cast("V", await auto_aiter(seq).__anext__())
    except StopAsyncIteration:
        return environment.undefined("No first item, sequence was empty.")


@async_variant(filters.do_groupby)
async def do_groupby(
    environment: "Environment",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    attribute: t.Union[str, int],
    default: t.Optional[t.Any] = None,
) -> "t.List[t.Tuple[t.Any, t.List[V]]]":
    expr = filters.make_attrgetter(environment, attribute, default=default)
    return [
        filters._GroupTuple(key, await auto_to_seq(values))
        for key, values in groupby(sorted(await auto_to_seq(value), key=expr), expr)
    ]


@async_variant(filters.do_join)
async def do_join(
    eval_ctx: "EvalContext",
    value: t.Union[t.AsyncIterable, t.Iterable],
    d: str = "",
    attribute: t.Optional[t.Union[str, int]] = None,
) -> str:
    return filters.do_join(eval_ctx, await auto_to_seq(value), d, attribute)


@async_variant(filters.do_list)
async def do_list(value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]") -> "t.List[V]":
    return await auto_to_seq(value)


@async_variant(filters.do_reject)
async def do_reject(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: not x, False)


@async_variant(filters.do_rejectattr)
async def do_rejectattr(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: not x, True)


@async_variant(filters.do_select)
async def do_select(
    context: "Context",
    value: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
    *args: t.Any,
    **kwargs: t.Any,
) -> "t.AsyncIterator[V]":
    return async_select_or_reject(context, value, args, kwargs, lambda x: x, False)


@async_variant(filters.do_selectattr)
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


@async_variant(filters.do_map)
async def do_map(context, value, *args, **kwargs):
    if value:
        func = filters.prepare_map(context, args, kwargs)

        async for item in auto_aiter(value):
            yield await auto_await(func(item))


@async_variant(filters.do_sum)
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


@async_variant(filters.do_slice)
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
