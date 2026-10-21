import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, overload

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from natcashify.core import Callback, InvalidSignatureError
from natcashify.django.clients import get_client

type SyncView = Callable[..., HttpResponse]
type AsyncView = Callable[..., Awaitable[HttpResponse]]


def _verify(request: HttpRequest) -> Callback | None:
    params = {key: request.GET.getlist(key) for key in request.GET}
    try:
        return get_client().parse_callback(params)
    except InvalidSignatureError:
        return None


@overload
def natcash_callback(view: AsyncView) -> AsyncView: ...
@overload
def natcash_callback(view: SyncView) -> SyncView: ...
def natcash_callback(view: Any) -> Any:
    if inspect.iscoroutinefunction(view):

        @wraps(view)
        async def async_wrapper(request: HttpRequest, *args: object, **kwargs: object) -> Any:
            callback = _verify(request)
            if callback is None:
                return HttpResponseBadRequest("Invalid NatCash callback")
            return await view(request, callback, *args, **kwargs)

        return async_wrapper

    @wraps(view)
    def sync_wrapper(request: HttpRequest, *args: object, **kwargs: object) -> Any:
        callback = _verify(request)
        if callback is None:
            return HttpResponseBadRequest("Invalid NatCash callback")
        return view(request, callback, *args, **kwargs)

    return sync_wrapper
