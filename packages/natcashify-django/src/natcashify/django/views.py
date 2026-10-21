import inspect
from collections.abc import Awaitable, Callable, Mapping
from functools import wraps
from typing import Any, Concatenate, cast, overload

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from natcashify.core import Callback, InvalidSignatureError
from natcashify.django.clients import get_async_client, get_client

type Parser = Callable[[Mapping[str, list[str]]], Callback]


def _verify(request: HttpRequest, parse: Parser) -> Callback | None:
    params = {key: request.GET.getlist(key) for key in request.GET}
    try:
        return parse(params)
    except InvalidSignatureError:
        return None


@overload
def natcash_callback[**P](
    view: Callable[Concatenate[HttpRequest, Callback, P], Awaitable[HttpResponse]],
) -> Callable[Concatenate[HttpRequest, P], Awaitable[HttpResponse]]: ...
@overload
def natcash_callback[**P](
    view: Callable[Concatenate[HttpRequest, Callback, P], HttpResponse],
) -> Callable[Concatenate[HttpRequest, P], HttpResponse]: ...
def natcash_callback(view: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(view):
        async_view = cast("Callable[..., Awaitable[HttpResponse]]", view)

        @wraps(async_view)
        async def async_wrapper(
            request: HttpRequest, *args: object, **kwargs: object
        ) -> HttpResponse:
            callback = _verify(request, get_async_client().parse_callback)
            if callback is None:
                return HttpResponseBadRequest("Invalid NatCash callback")
            return await async_view(request, callback, *args, **kwargs)

        return async_wrapper

    @wraps(view)
    def sync_wrapper(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        callback = _verify(request, get_client().parse_callback)
        if callback is None:
            return HttpResponseBadRequest("Invalid NatCash callback")
        return view(request, callback, *args, **kwargs)

    return sync_wrapper
